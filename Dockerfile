FROM quay.io/qiime2/metagenome:2024.10

# Для интерактивного дебага
RUN conda install -y -c conda-forge jupyterlab && conda clean -a


# Это, строго говоря, ненужный хлам, но пусть полежит
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


ENV PATH /opt/conda/bin:$PATH

COPY ./src /usr/local/bin/metagenimics16/src
COPY main.py /usr/local/bin/metagenimics16/


RUN chmod +x /usr/local/bin/metagenimics16/main.py*

WORKDIR /host_pwd
EXPOSE 8080

ENTRYPOINT [ "jupyter-lab" ]
CMD ["--allow-root", "--port", "8080", "--ip=0.0.0.0", "--no-browser"]
