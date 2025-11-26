"""
Processamento genérico de arquivos S3 -> ECS Task
Autor: Leandro Alves
Descrição: Função principal para processamento de arquivos genéricos
           e bloco principal para execução via ECS (Amazon ECS Task).
"""
import os
import json
import argparse
import json
import boto3
import pandas as pd
from datetime import datetime, timezone, timedelta
import numpy as np
from io import StringIO
from pathlib import Path
import re
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
import base64
from typing import Optional, Dict
#from special_functions import * # Verificar como irei chamar esse arquivo
# Modularização do codigo
import get_secrets # importando get_secrets.py
import get_number_of_columns # importando a função de contagem de colunas

# Diversas Variaveis
# --- Defina suas configurações para LocalStack aqui ---
LOCALSTACK_ENDPOINT_URL = "https://localstack.sumifit.business"
LOCALSTACK_AWS_ACCESS_KEY_ID = "test"  # LocalStack ignora, mas o Boto3 precisa
LOCALSTACK_AWS_SECRET_ACCESS_KEY = "test" # LocalStack ignora, mas o Boto3 precisa
# ------------------------------------------------------

# ============================================================
# Função principal: process_file_generic
# ============================================================

def process_file_generic(parameters, bucket_name, path_local_landing_zone, table_name, file_size_mb):
    """Processa arquivos genéricos de forma parametrizada."""

    try:
        # -------------------------------------------------------------------
        # Captura data e hora do início do processamento
        # -------------------------------------------------------------------
        uruguay_tz = timezone(timedelta(hours=-3))
        processing_start = datetime.now(uruguay_tz).strftime("%Y-%m-%d %H:%M:%S")

        # Parâmetros principais
        param_key = parameters.get("name", "")
        file_path = parameters.get("specific_file", "")
        print(f"# Key name (DYNAMODB) => {param_key}")

        # Diretório S3 base
        path_to_table = f"s3://{bucket_name}/landing-zone/{path_local_landing_zone}/"
        print(f"Diretório S3: {path_to_table}")

        # Limpeza da área de tracking
        clear_s3_directory(bucket_name, "tracking/")

        # -------------------------------------------------------------------
        # Processamento de arquivo específico
        # -------------------------------------------------------------------
        str_arquivo = file_path.split("/")[-1]
        print(f"Arquivo a ser processado: {str_arquivo}")

        path_file_full = f"s3://{bucket_name}/{file_path}"
        print(f"Caminho completo: {path_file_full}")

        # -------------------------------------------------------------------
        # Leitura e definição de parâmetros do arquivo
        # -------------------------------------------------------------------
        extension_file = parameters.get("extension_file", "CSV")
        separator_file_read = parameters.get("separator_file_read", None)
        if separator_file_read in ("", None):
            separator_file_read = None
        elif separator_file_read == "NULL":
            separator_file_read = None

        widths_param = parameters.get("widths", None)
        columns_names = parameters.get("columns_names", "")
        skip_rows = int(parameters.get("skip_rows", 0))

        print(f"Tipo de arquivo: {extension_file}")
        print(f"Separador: {separator_file_read}")
        print(f"Skip rows: {skip_rows}")
        print(f"Colunas: {columns_names}")

        # -------------------------------------------------------------------
        # Função auxiliar interna para checar número de colunas
        # -------------------------------------------------------------------
        def get_number_of_columns(file_path, is_fixed_width=False):
            try:
                if skip_rows == 0:
                    if is_fixed_width:
                        widths_str = json.loads(widths_param)
                        return len(widths_str)
                    else:
                        header_df = pd.read_csv(
                            file_path,
                            sep=parameters.get("separator_file_read", ","),
                            encoding=parameters.get("encoding_file_read", "utf-8"),
                            nrows=1,
                            dtype=str
                        )
                        return len(header_df.columns)
                else:
                    return len(columns_names.split(",")) if columns_names else 0
            except Exception as e:
                print(f"Erro ao determinar número de colunas: {e}")
                send_mail_exception()
                return 0

        # -------------------------------------------------------------------
        # Verifica tipo de arquivo e lê conteúdo
        # -------------------------------------------------------------------
        if extension_file.lower() in ["dat", "txt"] and separator_file_read is None:
            print("##### Processando arquivos posicionais #####")
            n_cols = get_number_of_columns(path_file_full, is_fixed_width=True)
            widths_str = json.loads(widths_param)

            data = pd.read_fwf(
                path_file_full,
                widths=widths_str[:n_cols],
                encoding=parameters.get("encoding_file_read", "utf-8"),
                skiprows=skip_rows,
                names=columns_names.split(",") if columns_names else None,
                dtype=str
            )

        elif extension_file.lower() in ["csv", "txt", "lis", "dat"]:
            print("##### Processando arquivos delimitados #####")
            n_cols = get_number_of_columns(path_file_full, is_fixed_width=False)
            data = pd.read_csv(
                path_file_full,
                sep=parameters.get("separator_file_read", ","),
                encoding=parameters.get("encoding_file_read", "utf-8"),
                dtype=str,
                skiprows=skip_rows,
                names=columns_names.split(",") if columns_names else None
            )

            if data.shape[1] != n_cols:
                print(f"Aviso: O arquivo tem {data.shape[1]} colunas, esperadas {n_cols}")
                data = data.iloc[:, :n_cols]

        # -------------------------------------------------------------------
        # Limpeza e estatísticas
        # -------------------------------------------------------------------
        data.columns = data.columns.str.strip()
        data = data.apply(clean_column)
        current_time = datetime.now(uruguay_tz)

        s3_client = boto3.client('s3')
        try:
            file_info = s3_client.head_object(Bucket=bucket_name, Key=file_path)
            file_creation_time = file_info["LastModified"].strftime("%Y-%m-%d %H:%M:%S")
            modification_time = file_info["LastModified"].strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Erro ao obter informações do arquivo: {e}")
            file_creation_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            modification_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # -------------------------------------------------------------------
        # Estatísticas iniciais
        # -------------------------------------------------------------------
        stats_data = {
            "bucket_name": bucket_name,
            "path_local": "/".join(file_path.split("/")[:-1]),
            "filename_path_local": str_arquivo,
            "validated_files_source": "Válido",
            "file_creation_date": file_creation_time,
            "modification_date": modification_time,
            "file_size_mb": file_size_mb,
            "table_name": table_name
        }

        save_statistics_initial(bucket_name, path_local_landing_zone, stats_data)

        # -------------------------------------------------------------------
        # Aplicando funções operacionais
        # -------------------------------------------------------------------
        print("### Iniciando configuração das funções operacionais ###")
        pd.set_option('display.max_columns', None)

        if "add_columns" in parameters and parameters["add_columns"] != "NULL":
            data = add_columns(data, parameters["add_columns"])

        if "rename_columns" in parameters and parameters["rename_columns"] != "NULL":
            rename_mapping = dict(pair.split(":") for pair in parameters["rename_columns"].split(","))
            data = rename_columns(data, rename_mapping)

        if "date_format" in parameters and parameters["date_format"] != "NULL":
            data = date_format(data, parameters["date_format"])

        if "hash_columns" in parameters and parameters["hash_columns"] != "NULL":
            data = apply_hash(data, parameters["hash_columns"])

        if "special_functions" in parameters and parameters["special_functions"] != "NULL":
            data = apply_special_functions(data, parameters["special_functions"])

        if "drop_columns" in parameters and parameters["drop_columns"] != "NULL":
            drop_list = parameters["drop_columns"].split(",")
            data = drop_columns(data, drop_list)

        if int(parameters.get("delete_last_row", 0)) > 0:
            data = data.iloc[:-1]

        # -------------------------------------------------------------------
        # Salvar arquivo processado no S3
        # -------------------------------------------------------------------
        regex_pattern = parameters.get("regex_pattern", "NULL")
        filename_output = parameters.get("filename_output", "NULL")
        path_s3 = parameters.get("path_s3", "PATH_ERROR")

        nome_saida = filename_output
        extension_file_target = parameters.get("extension_file_target", "csv")

        if nome_saida.startswith("Regex"):
            print("ATENÇÃO: verificar o REGEX no DYNAMODB!")
            mark_object_zero_byte(bucket_name, file_path)

        filename_s3 = f"transient-zone/{path_s3}/{nome_saida}.{extension_file_target.lower()}"

        if float(file_size_mb) > 4500:
            print("########## LARGE FILE ##########")
            save_largefile_to_s3_transient_zone(bucket_name, filename_s3, data)
            mark_object_zero_byte(bucket_name, file_path)
        else:
            print("########## REGULAR FILE ##########")
            save_to_s3_transient_zone(bucket_name, filename_s3, data)
            mark_object_zero_byte(bucket_name, file_path)

        # -------------------------------------------------------------------
        # Estatísticas finais e encerramento
        # -------------------------------------------------------------------
        processing_end = datetime.now(uruguay_tz).strftime("%Y-%m-%d %H:%M:%S")
        save_statistics_final(bucket_name, path_local_landing_zone, stats_data)
        generate_tracking_results(bucket_name)

    except Exception as e:
        error_message = f"Erro ao processar o arquivo {file_path}: {e}"
        print(error_message)
        send_mail_exception(
            file_name=file_path,
            process_name="process_file_generic",
            error_type=type(e).__name__,
            additional_info=str(e)
        )
        raise

    # ============================================================
# Bloco principal
# ============================================================

if __name__ == "__main__":
    print("### INICIANDO O PROCESSAMENTO NA ECS TASK ###")

    #parser = argparse.ArgumentParser(description="Processar parâmetros de entrada.")
    #parser.add_argument('--bucket_name', type=str, required=True)
    #parser.add_argument('--file_path', type=str, required=True)
    #parser.add_argument('--path_local', type=str, required=True)
    #parser.add_argument('--file_size_mb', type=str, required=True)
    #parser.add_argument('--table_name', type=str, required=True)
    #args = parser.parse_args()

#    bucket_name = args.bucket_name
#    file_path = args.file_path
#    path_local_landing_zone = args.path_local
#    file_size_mb = args.file_size_mb
#    table_name = args.table_name

    bucket_name = "datalake-dev"
    folder = "landing-zone"
    sub_folder = "oca-digital"
    process = "alta-celulares"
    file_path = f"landing-zone/oca-digital/alta-celulares/"
    path_local_landing_zone = f"{sub_folder}/{process}"
    file_size_mb = ""
    table_name = f"tbl_{process}"


    print(f"bucket_name: {bucket_name}")
    print(f"file_path: {file_path}")
    print(f"path_local: {path_local_landing_zone}")
    print(f"file_size_mb: {file_size_mb}")
    print(f"table_name: {table_name}")

    # Recupera parâmetros no S3
    job_run_id = "EcsJob"
    job_name = "EcsTask"
    s3_key = f"parameters/latam_parameter_{path_local_landing_zone.replace('/','_').lower()}.json"
    print(f"s3://{bucket_name}/{s3_key}")

    #try:
    #    parameters = load_json_s3(bucket_name, s3_key)
    #    if parameters:
    #        parameters["specific_file"] = file_path
    #        process_file_generic(parameters, bucket_name, path_local_landing_zone, table_name, file_size_mb)
    #    else:
    #        print("Nenhum parâmetro encontrado no arquivo JSON.")
    #except Exception as e:
    #    error_message = f"Erro na execução principal: {e}"
    #    print(error_message)
    #    send_mail_exception(
    #        file_name=file_path,
    #        process_name="main",
    #        error_type=type(e).__name__,
    #        additional_info=error_message
    #    )
    #    raise