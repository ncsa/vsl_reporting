FROM python:3

ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /vsl
COPY . /vsl
RUN python -m pip install -r /vsl/requirements.txt

CMD ["bash"]
