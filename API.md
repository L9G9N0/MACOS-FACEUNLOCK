# API Specification: IPC Socket Protocol

This document defines the interface contract, payloads, and socket transmission rules for the macOS FaceUnlock platform.

---

## 1. IPC Protocol Details

The system uses a single-event UNIX domain socket client/server communication architecture.

| Parameter | Specification |
| :--- | :--- |
| **Transport Protocol** | UNIX Domain Stream Socket (`AF_UNIX`, `SOCK_STREAM`) |
| **Socket Path** | `~/.faceunlock_run/faceunlock.sock` (Dynamically mapped using user home directory) |
| **Data Payload Encoding** | UTF-8 Plaintext |
| **Connection Lifespan** | Instantaneous connection, transmission, and termination |

---

## 2. API Schema

Once identity and liveness have been verified, the client daemon sends a single string payload.

### Payload Schema
```text
AUTH_SUCCESS_<username>
```

- **`<username>`**: The system username of the successfully matched profile (e.g., `hariom`).

### Example Payload
```text
AUTH_SUCCESS_hariom
```

---

## 3. Communication Lifecycle Flow

```text
PAM Server Socket (Listening)                   Client Daemon (Vision Loop)
      |                                                     |
      | <============ TCP-like Connection Handshake ========| (connect)
      |                                                     |
      | [getsockopt LOCAL_PEERCRED Check]                   |
      |                                                     |
      | <============ AUTH_SUCCESS_<username> ==============| (sendall)
      |                                                     |
      | ============= Connection Terminated ===============>| (close)
```

1. **Client Connection**: The client daemon opens a connection to the socket path defined in configuration settings.
2. **Peer creds confirmation**: The PAM module reads connection properties and verifies that the process UID matches the expected target logging user.
3. **Payload transmission**: The client daemon transmits the encoded string.
4. **Disconnection**: The client daemon calls `close()`. The PAM server deletes/unlinks the socket path.
