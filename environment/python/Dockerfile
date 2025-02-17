FROM python:3.9-buster  AS python-base

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/get/"
COPY ./ /get
VOLUME ["/get"]

RUN ls -l get

# Install pip-tools and compile requirements
RUN pip install --no-cache-dir pip-tools
RUN pip-compile /get/requirements.in

# Install Python dependencies
RUN pip install --no-cache-dir -r /get/requirements.txt

# cleaning
RUN rm -rf /root/.cache/pip && echo "Cache removed"
RUN apt-get clean pt-get autoremove -y && echo "APT cleaned, Autoremove done"
RUN rm -rf /var/lib/apt/lists/* /var/tmp/* /tmp/* && echo "Cleanup done"

