# Docker Setup for bghosal/herald

This guide explains how to build, run, and push the Docker image for the `bghosal/herald` application.

## Prerequisites

Ensure you have the following installed on your system:

- [Docker](https://www.docker.com/)
- A Docker Hub account (for pushing the image)

## Steps

### 1. Build the Docker Image

Use the following command to build the Docker image locally:

```bash
docker build -t bghosal/herald:0.0.1.RELEASE .
```

This command creates a Docker image tagged as `bghosal/herald` with version `0.0.1.RELEASE`.

### 2. Run the Docker Container

Run the Docker container using the following command:

```bash
docker container run -d -p 5000:5000 bghosal/herald:0.0.1.RELEASE
```

- `-d`: Runs the container in detached mode.
- `-p 5000:5000`: Maps port `5000` on your host to port `5000` in the container.

Once the container is running, the application should be accessible at `http://localhost:5000`.

### 3. Push the Docker Image to Docker Hub

To push the Docker image to Docker Hub, use the following command:

```bash
docker push bghosal/herald:0.0.1.RELEASE
```

Ensure you are logged in to Docker Hub before pushing the image. You can log in using:

```bash
docker login
```

### Additional Notes

- Make sure the `Dockerfile` is correctly set up to copy and configure your application files.
- Update the tag version (`0.0.1.RELEASE`) as needed for new releases.
- Use `docker container ls` to verify if the container is running.
- Use `docker logs <container_id>` to check the application logs if needed.

## Common Docker Commands

- Stop a running container:
  ```bash
  docker container stop <container_id>
  ```

- Remove a container:
  ```bash
  docker container rm <container_id>
  ```

- Remove an image:
  ```bash
  docker image rm bghosal/herald:0.0.1.RELEASE
  ```

- List all running containers:
  ```bash
  docker container ls
  ```

- List all images:
  ```bash
  docker image ls
  ```

## Troubleshooting

- If you encounter permission issues while building or running Docker commands, use `sudo` before the commands (Linux systems).
- Ensure that port `5000` is not in use by other applications on your host system.
- Verify the `Dockerfile` for syntax errors or missing files if the build fails.

For further assistance, refer to the [Docker documentation](https://docs.docker.com/).

