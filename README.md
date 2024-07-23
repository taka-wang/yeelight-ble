# yeelight-ble

A Dockerized daemon for controlling Yeelight devices using Bluetooth, tailored for Homebridge personal use.

## Installation

### 1. Build the Docker Image

Build the Docker image with the following command:

```sh
docker build --platform linux/arm/v7 -t yeelight-app .
```

### 2. Run the Docker Container

Start the Docker container with:

```sh
docker run -d --name=yeelight-app --net=host --privileged \
  --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --cap-add=NET_RAW \
  -v /var/run/dbus:/var/run/dbus \
  yeelight-app
```

- `--net=host`: Uses the host's network stack for direct Bluetooth communication.
- `--privileged`: Grants the container elevated permissions needed for Bluetooth operations.
- `--cap-add=NET_ADMIN`, `--cap-add=SYS_ADMIN`, `--cap-add=NET_RAW`: Adds capabilities required for network and system administration tasks.
- `-v /var/run/dbus:/var/run/dbus`: Mounts the D-Bus socket for inter-process communication.

## Usage

Control the Yeelight device using HTTP requests. Examples using `curl`:

1. Turn the lamp on:

   ```sh
   curl http://localhost:9090/on
   ```

2. Turn the lamp off:

   ```sh
   curl http://localhost:9090/off
   ```

3. Get the current status:

   ```sh
   curl http://localhost:9090/status
   ```

4. Set brightness to a specific value (1-100):

   ```sh
   curl http://localhost:9090/brightness?value=50
   ```

5. Increase brightness:

   ```sh
   curl http://localhost:9090/up
   ```

6. Decrease brightness:

   ```sh
   curl http://localhost:9090/down
   ```

## References

- [hass-yeelightbt](https://github.com/hcoohb/hass-yeelightbt)
- [python-yeelightbt](https://github.com/rytilahti/python-yeelightbt)

---
