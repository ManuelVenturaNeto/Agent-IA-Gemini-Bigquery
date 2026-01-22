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

```sql
-- Schema Creation
CREATE SCHEMA IF NOT EXISTS `<YOUR_PROJECT>.test_ia` OPTIONS (location = "us-central1");

-- Users Table
CREATE OR REPLACE TABLE `<YOUR_PROJECT>.test_ia.users` (
  id INT64, 
  nome STRING, 
  email STRING, 
  company_id INT64
);

-- Data Insertion (50 Automatic + 1 Manual)
INSERT INTO `<YOUR_PROJECT>.test_ia.users` (id, nome, email, company_id)
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
),
base AS (
    SELECT id FROM UNNEST(GENERATE_ARRAY(1, 50)) AS id
)
SELECT 
    base.id, 
    CONCAT((SELECT arr[OFFSET(MOD(base.id - 1, ARRAY_LENGTH(arr)))] FROM first_names), ' ', (SELECT arr[OFFSET(MOD(base.id * 3, ARRAY_LENGTH(arr)))] FROM last_names)), 
    FORMAT('user%03d@empresa.com', base.id), 
    1001 + MOD(base.id - 1, 8) 
FROM base
UNION ALL SELECT 6666, 'Manuel Ventura', 'manuueelneto@gmail.com', 1;

-- Flight Tickets Table
CREATE OR REPLACE TABLE `<YOUR_PROJECT>.test_ia.passagens_aereas` (
  id INT64, 
  protocolo STRING, 
  company_id INT64, 
  data_ida DATE, 
  data_volta DATE, 
  preco_ida NUMERIC, 
  preco_volta NUMERIC
);

-- Ticket Insertion (200 Automatic + 1 Manual)
INSERT INTO `<YOUR_PROJECT>.test_ia.passagens_aereas` (id, protocolo, company_id, data_ida, data_volta, preco_ida, preco_volta)
WITH base AS (
    SELECT id FROM UNNEST(GENERATE_ARRAY(1, 200)) AS id
),
datas AS (
    SELECT id, DATE_ADD(DATE '2026-01-01', INTERVAL id DAY) AS data_ida FROM base
)
SELECT 
    datas.id, 
    FORMAT('ONF-%s-%06d', FORMAT_DATE('%Y%m', datas.data_ida), datas.id), 
    1001 + MOD(datas.id - 1, 8), 
    datas.data_ida, 
    DATE_ADD(datas.data_ida, INTERVAL (2 + MOD(datas.id, 14)) DAY), 
    (CAST(150 + MOD(datas.id * 97, 2200) AS NUMERIC) + (CAST(MOD(datas.id * 13, 100) AS NUMERIC) / 100)), 
    (CAST(150 + MOD(datas.id * 131, 2400) AS NUMERIC) + (CAST(MOD(datas.id * 29, 100) AS NUMERIC) / 100)) 
FROM datas
UNION ALL SELECT 666, 'ONF-202602-000666', 1, DATE '2025-12-31', DATE '2026-12-31', 666.66, 1001.00;
```