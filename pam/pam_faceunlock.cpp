#include <iostream>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <pwd.h>
#include <security/pam_appl.h>
#include <security/pam_modules.h>
#include <cstring>
#include <fcntl.h>

// PAM modules must explicitly define these macros
#define PAM_SM_AUTH
#define PAM_SM_ACCOUNT

#define TIMEOUT_SECONDS 5

extern "C" {

PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    const char *username = NULL;
    
    // 1. Retrieve the target logging-in username from PAM context
    if (pam_get_user(pamh, &username, NULL) != PAM_SUCCESS || username == NULL) {
        return PAM_IGNORE; // Fallback to password
    }

    // 2. Lookup user passwd details to find the correct home directory
    struct passwd *pw = getpwnam(username);
    if (pw == NULL) {
        return PAM_IGNORE;
    }

    uid_t target_uid = pw->pw_uid;
    gid_t target_gid = pw->pw_gid;
    const char *home_dir = pw->pw_dir;

    // 3. Construct socket path under the user's home directory
    char sock_path[1024];
    snprintf(sock_path, sizeof(sock_path), "%s/.faceunlock_run/faceunlock.sock", home_dir);

    // Clear previous stale sockets safely
    unlink(sock_path);

    // 4. Create UNIX Domain Socket
    int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) {
        return PAM_IGNORE;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, sock_path, sizeof(addr.sun_path) - 1);

    // 5. Bind the socket
    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        close(server_fd);
        return PAM_IGNORE;
    }

    // 6. Restrict File System Permissions to User-Only (0600)
    // chown to target user so root-created socket is owned by the authenticating user
    if (chown(sock_path, target_uid, target_gid) == -1) {
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }
    if (chmod(sock_path, 0600) == -1) {
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }

    // 7. Listen for connection
    if (listen(server_fd, 1) == -1) {
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }

    // 8. Timeout Await using select() to prevent lockouts
    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(server_fd, &read_fds);

    struct timeval tv;
    tv.tv_sec = TIMEOUT_SECONDS;
    tv.tv_usec = 0;

    int ready = select(server_fd + 1, &read_fds, NULL, NULL, &tv);
    if (ready <= 0) {
        // Await timed out
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }

    // 9. Accept client daemon
    int client_fd = accept(server_fd, NULL, NULL);
    if (client_fd < 0) {
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }

    // 10. Peer Verification: Verify that the client is owned by the authenticating user
    // On macOS, LOCAL_PEERCRED yields a struct xucred
    struct xucred {
        u_int cr_version;
        uid_t cr_uid;
        short cr_ngroups;
        gid_t cr_groups[16];
    } peer_cred;

    socklen_t optlen = sizeof(peer_cred);
    if (getsockopt(client_fd, 0, LOCAL_PEERCRED, &peer_cred, &optlen) == -1) {
        close(client_fd);
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }

    if (peer_cred.cr_uid != target_uid) {
        // Security Escalation: Connection from unprivileged local client blocked!
        close(client_fd);
        close(server_fd);
        unlink(sock_path);
        return PAM_AUTH_ERR;
    }

    // 11. Read Authentication payload
    char buffer[256];
    memset(buffer, 0, sizeof(buffer));
    int bytes_read = read(client_fd, buffer, sizeof(buffer) - 1);

    close(client_fd);
    close(server_fd);
    unlink(sock_path);

    char expected_signal[256];
    snprintf(expected_signal, sizeof(expected_signal), "AUTH_SUCCESS_%s", username);

    if (bytes_read > 0 && strstr(buffer, expected_signal) != NULL) {
        return PAM_SUCCESS;
    }

    return PAM_AUTH_ERR;
}

PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    return PAM_SUCCESS;
}

PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    return PAM_SUCCESS;
}

} // extern "C"