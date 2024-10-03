# langchain-python-rag-authz

An example CLI tool in Python that demonstrates how to integrate Pangea's
[AuthZ][] service into a LangChain app to filter out RAG documents based on user
permissions.

## Prerequisites

- Python v3.12 or greater.
- pip v24.2 or [uv][] v0.4.18.
- A [Pangea account][Pangea signup] with AuthZ enabled.
- An [OpenAI API key][OpenAI API keys].
- libmagic
  - macOS: `brew install libmagic`
  - Windows: included via the python-magic-bin package

The setup in AuthZ should look something like this:

### Resource types

| Name        | Permissions |
| ----------- | ----------- |
| engineering | read        |
| finance     | read        |

### Roles & access

> [!TIP]
> At this point you need to create 2 new Roles under the `Roles & Access` tab in the Pangea console named `engineering` and `finance`.

#### Role: engineering

| Resource type | Permissions (read) |
| ------------- | ------------------ |
| engineering   | ✔️                 |
| finance       | ❌                 |

#### Role: finance

| Resource type | Permissions (read) |
| ------------- | ------------------ |
| engineering   | ❌                 |
| finance       | ✔️                 |

### Assigned roles & relations

| Subject type | Subject ID | Role/Relation |
| ------------ | ---------- | ------------- |
| user         | alice      | engineering   |
| user         | bob        | finance       |

## Setup

```shell
git clone https://github.com/pangeacyber/langchain-python-rag-authz.git
cd langchain-python-rag-authz
```

If using pip:

```shell
python -m venv .venv
source .venv/bin/activate
pip install .
```

Or, if using uv:

```shell
uv sync
source .venv/bin/activate
```

The sample can then be executed with:

```shell
python -m langchain_rag_authz
```

## Usage

```
Usage: python -m langchain_rag_authz [OPTIONS] PROMPT

Options:
  --user TEXT              Unique username to simulate retrieval as.
                           [required]
  --authz-token SECRET     Pangea AuthZ API token. May also be set via the
                           `PANGEA_AUTHZ_TOKEN` environment variable.
                           [required]
  --pangea-domain TEXT     Pangea API domain. May also be set via the
                           `PANGEA_DOMAIN` environment variable.  [default:
                           aws.us.pangea.cloud; required]
  --model TEXT             OpenAI model.  [default: gpt-4o-mini; required]
  --openai-api-key SECRET  OpenAI API key. May also be set via the
                           `OPENAI_API_KEY` environment variable.  [required]
  --help                   Show this message and exit.
```

Assuming user "alice" has permission to see engineering documents, they can
query the LLM on information regarding those documents:

```
$ python -m langchain_rag_authz --user alice "What is the software architecture of the company?"

The company's software architecture consists of a frontend built with ReactJS,
Redux, and Axios, along with Material-UI for design components. The backend
utilizes Node.js and Express.js, with MongoDB as the database. Authentication
and authorization are managed through JSON Web Tokens (JWT) and OAuth 2.0, and
version control is handled using Git and GitHub.
```

But they cannot query finance information:

```
$ python -m langchain_rag_authz --user alice "What is the top salary in the Engineering department?"

I don't know.
```

And vice versa for "bob", who is in finance but not engineering.

[AuthZ]: https://pangea.cloud/docs/authz/
[Pangea signup]: https://pangea.cloud/signup
[OpenAI API keys]: https://platform.openai.com/api-keys
[uv]: https://docs.astral.sh/uv/
