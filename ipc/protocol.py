import os
import socket
from shared.utils import load_config, setup_logger

logger = setup_logger("IPC")

def send_auth_signal(username: str) -> bool:
    """Securely transmits the authorization success signal to the active PAM module listener socket.
    
    Args:
        username (str): The username of the successfully authenticated user.
        
    Returns:
        bool: True if the signal was successfully dispatched, False otherwise.
    """
    config = load_config()
    socket_path = config.get("socket_path")

    if not socket_path or not os.path.exists(socket_path):
        logger.debug(f"Active PAM listener socket absent at {socket_path} (Sudo/Screensaver not waiting).")
        return False

    try:
        # Create UNIX stream socket client
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(socket_path)
            
            # Formulate username-bound success signal matching C++ expectations
            signal = f"AUTH_SUCCESS_{username}".encode("utf-8")
            client.sendall(signal)
            logger.info(f"Successfully dispatched authenticated unlock signal for user: {username}")
            return True
    except Exception as e:
        logger.error(f"Failed to dispatch auth signal on socket: {str(e)}")
        return False

