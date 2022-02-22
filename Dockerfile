FROM amazonlinux:2
COPY requirements.txt /tmp/requirements.txt
RUN yum install -y postgresql postgresql-devel gcc python3-devel libpq-devel python3 python3-pip
RUN yum install -y libstdc++-devel gcc-c++ fuse fuse-devel curl-devel libxml2-devel openssl-devel
 
RUN python3 -m pip install \
        jupyter==1.0.0 \
        boto3==1.17.84 \
        PyYAML==5.4.1 \
        requests==2.26.0 \
        nbconvert==6.1.0 \
        nbformat==5.1.3 \
        ipython==7.25.0
 
RUN python3 -m pip install \
        -r /tmp/requirements.txt
 
# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case.
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
 
RUN mkdir -p /opt/ml/code
RUN mkdir -p ~/.aws
RUN ls -la /opt/ml/code
COPY convert_execute_notebook.py /opt/ml/code/convert_execute_notebook.py
COPY src/ /opt/ml/code/src/
ENV PYTHONPATH=/opt/ml/code/src
WORKDIR /opt/ml/code/
RUN ls -la /opt/ml/code/
