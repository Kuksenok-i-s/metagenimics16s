FROM quay.io/qiime2/amplicon:2024.10

# Для интерактивного дебага
RUN conda install -y -c conda-forge jupyterlab && conda clean -a

ENV PATH /opt/conda/bin:$PATH

COPY ./src /usr/local/bin/metagenimics16/src
COPY ./main.py /usr/local/bin/metagenimics16/


# Установка необходимых питонячих пакетов
COPY ./requirements.txt /usr/local/bin/metagenimics16/
RUN conda install -y -c conda-forge --file /usr/local/bin/metagenimics16/requirements.txt && conda clean -a

RUN chmod +x /usr/local/bin/metagenimics16/main.py*

WORKDIR /host_pwd
EXPOSE 8080

ENTRYPOINT [ "jupyter-lab" ]
CMD ["--allow-root", "--port", "8080", "--ip=0.0.0.0", "--no-browser"]
