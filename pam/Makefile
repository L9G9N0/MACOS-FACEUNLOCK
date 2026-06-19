# Compilation parameters for macOS Pluggable Authentication Module
CC = clang++
CFLAGS = -dynamiclib -fPIC -std=c++17 -O3
LDFLAGS = -lpam
TARGET = pam_faceunlock.so
SRC = pam_faceunlock.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET)
