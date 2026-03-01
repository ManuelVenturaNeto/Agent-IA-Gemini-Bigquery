# AI SQL Agent: BigQuery + Gemini

This project is an artificial intelligence agent designed to translate natural language questions into specific **Google BigQuery** SQL queries. The core differentiator of this agent is the **Security Wrapper** layer, which ensures that a user can never access data belonging to a company other than their own.

## 🗄️ 1. Database Preparation (Mocked Data)

The database simulates a travel management system. The script below prepares the environment in BigQuery within the `test_ia` dataset.

### Table Structure
* **`users`**: Stores name, email, and `company_id` (the link to the organization).
* **`passagens_aereas`**: Stores flight protocols, dates, and prices, also linked to a `company_id`.

[Image of a database schema showing a one-to-many relationship between users and passagens_aereas via company_id]

### Setup Script (SQL)
Run the code below in the BigQuery console to generate the test data (51 users and 201 flight records):

```.env
GEN_IA_KEY=<YOUR IA STUDIO KEY>
PROJECT=<YOUR PROJECT>
PROJECT_SA=<YOUR SERVICE ACCOUNT KEY FROM GCP>
```

```project-tree
├── src
│   ├── agents
│   │   ├── __init__.py
│   │   └── query_agent.py
│   ├── api
│   │   ├── __init__.py
│   │   └── app.py
│   ├── infra
│   │   ├── config
│   │   │   ├── config_google
│   │   │   │   ├── __init__.py
│   │   │   │   └── bigquery_maganger.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── main
│   │   ├── __init__.py
│   │   └── main.py
│   └── __init__.py
├── .gitignore
├── readme.md
├── run.py
└── schema_project.png
```


```sql
-- Schema Creation
CREATE SCHEMA IF NOT EXISTS `test_ia`
OPTIONS (location = "us-central1");

-- =========================================================
-- 1) TABELA: USUARIOS
-- =========================================================
CREATE OR REPLACE TABLE `test_ia.usuarios` (
    id INT64,
    nome STRING,
    email STRING,
    id_empresa INT64
);

INSERT INTO `test_ia.usuarios` (id, nome, email, id_empresa)
WITH first_names AS (
    SELECT ARRAY<STRING>[
        'Ana','Bruno','Carla','Daniel','Eduardo','Fernanda','Gabriel','Helena','Igor','Juliana',
        'Kleber','Larissa','Marcos','Natalia','Otavio','Patricia','Rafael','Sabrina','Tiago','Vanessa',
        'William','Yasmin','Beatriz','Caio','Debora','Fabio','Giovana','Hugo','Isabela','Joao',
        'Karen','Leandro','Mariana','Nicolas','Paula','Renato','Sara','Vitor','Wesley','Aline',
        'Cintia','Diego','Elaine','Felipe','Gustavo','Livia','Mateus','Priscila','Rodrigo','Tatiane'
    ] AS arr
),
last_names AS (
    SELECT ARRAY<STRING>[
      'Silva','Souza','Oliveira','Santos','Pereira','Lima','Carvalho','Ribeiro','Almeida','Gomes',
      'Martins','Ferreira','Rodrigues','Barbosa','Teixeira','Moura','Araujo','Monteiro'
    ] AS arr
)
,
base AS (
    SELECT 
        id 
    FROM UNNEST(GENERATE_ARRAY(1, 50)) AS id
)
SELECT
    base.id,
    CONCAT(
        (SELECT arr[OFFSET(MOD(base.id - 1, ARRAY_LENGTH(arr)))] FROM first_names),
        ' ',
        (SELECT arr[OFFSET(MOD(base.id * 3, ARRAY_LENGTH(arr)))] FROM last_names)) AS nome,
    FORMAT('user%03d@empresa.com', base.id) AS email,
    1001 + MOD(base.id - 1, 8) AS id_empresa
FROM base
UNION ALL
SELECT 6666, 'Manuel Ventura', 'manuueelneto@gmail.com', 1;

-- =========================================================
-- 2) TABELA: PASSAGENS_AEREAS
-- =========================================================
CREATE OR REPLACE TABLE `test_ia.passagens_aereas` (
    id INT64,
    protocolo STRING,
    id_empresa INT64,
    data_ida DATE,
    data_volta DATE,
    preco_ida NUMERIC,
    preco_volta NUMERIC
);

INSERT INTO `test_ia.passagens_aereas`
    (id, protocolo, id_empresa, data_ida, data_volta, preco_ida, preco_volta)
WITH base AS (
    SELECT 
        id 
    FROM UNNEST(GENERATE_ARRAY(1, 200)) AS id
),
datas AS (
    SELECT 
        id, 
        DATE_ADD(DATE '2026-01-01', INTERVAL id DAY) AS data_ida
    FROM base
)
SELECT
    datas.id,
    FORMAT('CODE-%s-%06d', FORMAT_DATE('%Y%m', datas.data_ida), datas.id) AS protocolo,
    1001 + MOD(datas.id - 1, 8) AS id_empresa,
    datas.data_ida AS data_ida,
    DATE_ADD(datas.data_ida, INTERVAL (2 + MOD(datas.id, 14)) DAY) AS data_volta,
    (CAST(150 + MOD(datas.id * 97, 2200) AS NUMERIC) + (CAST(MOD(datas.id * 13, 100) AS NUMERIC) / 100)) AS preco_ida,
    (CAST(150 + MOD(datas.id * 131, 2400) AS NUMERIC) + (CAST(MOD(datas.id * 29, 100) AS NUMERIC) / 100)) AS preco_volta
FROM datas
UNION ALL
SELECT 666, 'CODE-202602-000666', 1, DATE '2025-12-31', DATE '2026-12-31', 666.66, 1001.00;

-- =========================================================
-- 3) TABELA: EMPRESAS
-- =========================================================
CREATE OR REPLACE TABLE `test_ia.empresas` (
  id_empresa INT64,
  nome_empresa STRING,
  hash_empresa STRING
);

-- Exemplo de grupos de "dono":
-- dono_a: empresas 1001 e 1002 (mesmo hash)
-- dono_b: empresa 1003
-- dono_c: empresas 1004, 1005, 1006 (mesmo hash)
-- dono_d: empresas 1007, 1008 (mesmo hash)
-- dono_manual: empresa 1
INSERT INTO `test_ia.empresas` (id_empresa, nome_empresa, hash_empresa)
SELECT 1,    'Empresa Manuel', TO_HEX(SHA256(CAST('dono_manual' AS BYTES))) UNION ALL
SELECT 1001, 'Empresa 1001',   TO_HEX(SHA256(CAST('dono_a' AS BYTES)))      UNION ALL
SELECT 1002, 'Empresa 1002',   TO_HEX(SHA256(CAST('dono_a' AS BYTES)))      UNION ALL
SELECT 1003, 'Empresa 1003',   TO_HEX(SHA256(CAST('dono_b' AS BYTES)))      UNION ALL
SELECT 1004, 'Empresa 1004',   TO_HEX(SHA256(CAST('dono_c' AS BYTES)))      UNION ALL
SELECT 1005, 'Empresa 1005',   TO_HEX(SHA256(CAST('dono_c' AS BYTES)))      UNION ALL
SELECT 1006, 'Empresa 1006',   TO_HEX(SHA256(CAST('dono_c' AS BYTES)))      UNION ALL
SELECT 1007, 'Empresa 1007',   TO_HEX(SHA256(CAST('dono_d' AS BYTES)))      UNION ALL
SELECT 1008, 'Empresa 1008',   TO_HEX(SHA256(CAST('dono_d' AS BYTES)));

-- =========================================================
-- 4) TABELA: DESPESAS
-- =========================================================
CREATE OR REPLACE TABLE `test_ia.despesas` (
  id INT64,
  id_usuario INT64,
  id_empresa INT64,
  data_despesa DATE,
  categoria STRING,
  descricao STRING,
  valor NUMERIC,
  status STRING,
  protocolo STRING
);


INSERT INTO `test_ia.despesas`
    (id, id_usuario, id_empresa, data_despesa, categoria, descricao, valor, status, protocolo)
WITH categorias AS (
    SELECT ARRAY<STRING>[
        'Alimentação',
        'Gasoline',
        'Hospedagem',
        'Transporte',
        'Passagem Aérea',
        'Uber',
        'Reembolso',
    ] AS arr
)
,
status_arr AS (
    SELECT ARRAY<STRING>['APROVADA','PENDENTE','REPROVADA'] AS arr
)
,
base AS (
    SELECT 
        id 
    FROM UNNEST(GENERATE_ARRAY(1, 500)) AS id
)
,
base_enriched AS (
    SELECT
        base.id AS id,
        CASE WHEN MOD(base.id, 40) = 0 THEN 6666 ELSE (1 + MOD(base.id - 1, 50)) END AS id_usuario,
        CASE WHEN MOD(base.id, 40) = 0 THEN 1    ELSE (1001 + MOD(base.id - 1, 8)) END AS id_empresa,
        DATE_ADD(DATE '2026-01-01', INTERVAL MOD(base.id * 7, 180) DAY) AS data_despesa,
        (SELECT arr[OFFSET(MOD(base.id - 1, ARRAY_LENGTH(arr)))] FROM categorias) AS categoria,
        (SELECT arr[OFFSET(MOD(base.id - 1, ARRAY_LENGTH(arr)))] FROM status_arr) AS status
    FROM base
)
SELECT
    be.id,
    be.id_usuario,
    be.id_empresa,
    be.data_despesa,
    be.categoria,
    CONCAT('Despesa ', be.categoria, ' #', CAST(be.id AS STRING)) AS descricao,
    (CAST(20 + MOD(be.id * 37, 1500) AS NUMERIC) + (CAST(MOD(be.id * 19, 100) AS NUMERIC) / 100)) AS valor,
    be.status,
    IF(be.categoria = 'Passagem Aérea', pa.protocolo, NULL) AS protocolo
FROM base_enriched be
LEFT JOIN `test_ia.passagens_aereas` pa
    ON pa.id = 1 + MOD(be.id - 1, 200)
    AND pa.id_empresa = be.id_empresa

UNION ALL

SELECT
    999999,
    6666,
    1,
    DATE '2026-01-15',
    'Alimentação',
    'Jantar com cliente',
    189.90,
    'APROVADA',
    NULL
;
```


## Schema of the project

![Schema of the project](schema_project.png)