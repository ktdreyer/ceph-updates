# shortcuts for building and running containers with podman.

build:
	podman build -t ceph-updates .

run:
	# --network=host and --privileged are needed until
	# https://github.com/rootless-containers/slirp4netns/pull/61
	# is available in a slirp4netns build for my host OS (Fedora 29).
	podman run --network=host --privileged -p 8000:8000/tcp ceph-updates

.PHONY: build run
