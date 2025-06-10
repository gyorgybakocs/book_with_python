FROM python:3.12-bullseye  AS python-base

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/get/"

COPY ./requirements.in /tmp/requirements.in
COPY ./tests.sh tests.sh
RUN chmod +x tests.sh

# Install pip-tools and compile requirements
RUN pip install --no-cache-dir pip-tools && \
    pip install --no-cache-dir apryse-sdk --extra-index-url=https://pypi.apryse.com
RUN pip-compile /tmp/requirements.in

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# cleaning
RUN rm -rf /root/.cache/pip && echo "Cache removed"
RUN apt-get clean pt-get autoremove -y && echo "APT cleaned, Autoremove done"
# RUN rm -rf /var/lib/apt/lists/* /var/tmp/* /tmp/* && echo "Cleanup done"
