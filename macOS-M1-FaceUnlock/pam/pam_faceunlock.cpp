#include <iostream>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <sys/stat.h>
#include <security/pam_appl.h>
#include <security/pam_modules.h>
#include <cstring>

// PAM modules must explicitly define these macros
#define PAM_SM_AUTH
#define PAM_SM_ACCOUNT

// Safe timeout so you NEVER get locked out of your Mac
#define TIMEOUT_SECONDS 5

extern "C" {

PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    // Exact path matching your Python Vision Daemon
    const char* sock_path = "/Users/hariom/.faceunlock_run/faceunlock.sock";
    
    // 1. Create Unix Domain Socket
    int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) return PAM_IGNORE; // Fallback to typing password

    // Clear zombie sockets from previous runs
    unlink(sock_path); 
    
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, sock_path, sizeof(addr.sun_path)-1);
    
    // 2. Bind the socket
    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        close(server_fd);
        return PAM_IGNORE; 
    }
    
    // IMPORTANT: Let Python (running as user 'hariom') write to this socket (created by root PAM)
    chmod(sock_path, 0777); 
    
    // 3. Listen for Python Daemon
    if (listen(server_fd, 1) == -1) {
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }
    
    // 4. Implement 5-Second Timeout using select()
    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(server_fd, &read_fds);
    
    struct timeval tv;
    tv.tv_sec = TIMEOUT_SECONDS;
    tv.tv_usec = 0;
    
    // OS waits here. If you show your face within 5 seconds, it catches the signal.
    int ready = select(server_fd + 1, &read_fds, NULL, NULL, &tv);
    if (ready <= 0) {
        // Timeout! Face not found. Drop to normal password prompt.
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE; 
    }
    
    // 5. Accept Connection from Python
    int client_fd = accept(server_fd, NULL, NULL);
    if (client_fd < 0) {
        close(server_fd);
        unlink(sock_path);
        return PAM_IGNORE;
    }

    // 6. Read the IPC Signal
    char buffer[256];
    memset(buffer, 0, sizeof(buffer));
    int bytes_read = read(client_fd, buffer, sizeof(buffer)-1);
    
    // Cleanup Network buffers
    close(client_fd);
    close(server_fd);
    unlink(sock_path);
    
    // 7. THE GOLDEN CHECK
    if (bytes_read > 0 && strstr(buffer, "AUTH_SUCCESS_HARIOM") != NULL) {
        // BOOM! Tell macOS Kernel to UNLOCK THE SYSTEM!
        return PAM_SUCCESS; 
    }
    
    return PAM_AUTH_ERR;
}

// macOS requires these standard callbacks for a valid PAM module
PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    return PAM_SUCCESS;
}
PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    return PAM_SUCCESS;
}

} // extern "C"