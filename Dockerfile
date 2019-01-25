FROM centos:7

# Install Python 3
RUN yum -y install centos-release-scl && \
   yum -y --setopt skip_missing_names_on_install=False install rh-python36

# Add CentOS user
RUN useradd --create-home --shell /bin/bash centos

# Install system dependencies for Pecan and Koji client
RUN yum -y install krb5-devel rpm-devel gcc python-devel

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

COPY koji.conf.d/cbs-koji.conf /home/centos/.koji/config.d/cbs-koji.conf

RUN scl enable rh-python36 -- pip install -r requirements.txt

COPY . /app

USER centos
EXPOSE 8080

ENTRYPOINT [ "scl", "enable", "rh-python36", "--", "gunicorn_pecan" ]

CMD [ "config.py" ]
