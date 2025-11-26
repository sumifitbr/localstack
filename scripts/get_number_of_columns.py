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