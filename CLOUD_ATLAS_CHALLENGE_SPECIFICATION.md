# Teste Técnico — Cloud Atlas

> Transcrição em Markdown do documento original fornecido para o desafio técnico. A estrutura foi adaptada apenas para legibilidade em Markdown; o conteúdo e os requisitos foram preservados.

## Objetivo

Criar uma API para gerenciamento de Tags.

## Motivo

O gerenciamento de Tags é importante para classificação dos recursos criados na Cloud, sendo seu principal benefício entregar uma visão de custo agrupada.

## Regras de Negócio

1. Tags e seus Values são entidades que formam um par chave-valor.

   Exemplo: `team: atlas`

   a. As Tags são únicas por usuário.  
   b. Values são únicos por Tag.  
   c. Tags podem ter mais de um valor associado.

2. Os identificadores das entidades devem ser do tipo UUID.

3. Os campos que representam nomes devem:

   a. possuir somente letras minúsculas, números, underline (`_`) ou traço (`-`).

   Exemplo: `squad-cat`

   b. conter no mínimo 3 caracteres e no máximo 64 caracteres.

4. O campo de descrição deve ser opcional.

5. Cada usuário só poderá visualizar e manipular as entidades criadas por ele mesmo.

## Requisitos

1. O desenvolvimento dessa API deve ser feito preferencialmente na linguagem Python com FastAPI, mas pode ser usada a linguagem que você é fluente.

2. Use um banco de dados relacional, preferencialmente PostgreSQL.

3. Desenvolver endpoints seguindo o padrão REST para:

   a. Tags

   i. Listar Tags  
   ii. Criar uma Tag  
   iii. Obter uma Tag  
   iv. Atualizar Tag  
   v. Remover Tag

   b. Values

   i. Listar Values de uma Tag  
   ii. Criar Value para uma Tag  
   iii. Obter Value de uma Tag  
   iv. Atualizar Value de uma Tag  
   v. Remover Value de uma Tag

4. Para as operações de Tags:

   a. Todas as operações deverão retornar as Tags contendo pelo menos os seguintes campos:

```json
{
  "id": "39e77112-bb38-475f-9e94-d3a27fe80c46",
  "name": "nome-da-tag",
  "description": "Descrição da tag.",
  "values": [
    {
      "id": "af8ad0b1-47d1-4b63-8f38-e70612d3342c",
      "name": "nome-do-valor",
      "description": "Descrição do valor."
    }
  ]
}
```

   b. Deverá ser possível criar uma Tag já contendo seus Values.

   c. Ao remover uma Tag, seus Values deverão ser removidos também.

5. Para as operações de Values:

   a. Todas as operações deverão retornar os Values contendo pelo menos os seguintes campos:

```json
{
  "id": "af8ad0b1-47d1-4b63-8f38-e70612d3342c",
  "name": "nome-do-valor",
  "description": "Descrição do valor."
}
```

6. O identificador do usuário deverá ser passado obrigatoriamente via header nas requisições. Não será necessário criar uma entidade para representá-lo nessa API.

7. Implementar testes para garantir o funcionamento do aplicação.

8. Documentar no readme como utilizar sua API.

9. Prover um Dockerfile para o deploy da aplicação.

## Extras

Caso tenha alguma ideia de melhoria para essa API, fique a vontade para implementar.
