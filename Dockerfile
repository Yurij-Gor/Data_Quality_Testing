# Use the base Python image
FROM python:3.12

WORKDIR /tests_project/

COPY requirements.txt .

RUN pip install -r requirements.txt

# Copy all project files into the working directory of the container
COPY . .

# Install Google Cloud SDK
RUN apt-get update && apt-get install -y curl gnupg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update && apt-get install -y google-cloud-sdk

# Install Allure CLI
RUN wget https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.27.0/allure-commandline-2.27.0.tgz -O allure-commandline.tgz && \
    tar -zxvf allure-commandline.tgz -C /opt/ && \
    ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure && \
    rm -f allure-commandline.tgz

ENV RUN_IN_DOCKER=true

RUN mkdir -p test_results/

CMD ["python", "-m", "pytest", "-vv", "-s", "--alluredir=test_results/", "tests/"]
