FROM r-base:4.4.1

RUN R -e "install.packages(c('tidyverse', 'data.table', 'jsonlite', 'arrow'), repos='https://cloud.r-project.org')"

RUN useradd -m -s /bin/bash runner
USER runner

WORKDIR /home/runner
