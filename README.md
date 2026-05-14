# Code Reviewer — Desktop App

App de code review de diffs usando Groq API + interface gráfica em Python.

## Gerar arquivo diff
- git diff dev -w > C:\icaro\diffs\NomeDoArquivo.diff

## Pré-requisitos

- Python 3.13 instalado com a opção **"Add python.exe to PATH"** marcada
- Uma API Key do Groq (obtenha em https://console.groq.com)

---

## 1. Instalar dependências

Abra o **Prompt de Comando** na pasta do projeto:

```cmd
python -m pip install customtkinter groq pyinstaller
```

---

## 2. Configurar a API Key

Você tem duas opções:

**Opção A — arquivo .env (recomendado):**
Renomeie o `.env.example` para `.env` e cole sua chave:
```
GROQ_API_KEY=gsk_sua_chave_aqui
```
A chave será carregada automaticamente toda vez que abrir o app.

**Opção B — pela interface:**
Digite a chave no campo do app e clique em **💾 Salvar** — ela será gravada no `.env` automaticamente.

---

## 3. Rodar o app

```cmd
python -m code_reviewer
```

---

## 4. Gerar o executável (.exe)

**Passo 1** — Descubra o caminho do customtkinter na sua máquina:

```cmd
python -c "import customtkinter, os; print(os.path.dirname(customtkinter.__file__))"
```

Exemplo de saída:
```
C:\Users\icaro\AppData\Local\Programs\Python\Python313\Lib\site-packages\customtkinter
```

**Passo 2** — Gere o executável substituindo o caminho pelo que apareceu acima:

```cmd
python -m PyInstaller --onefile --windowed --name "CodeReviewer" --add-data "C:\Users\icaro\AppData\Local\Programs\Python\Python313\Lib\site-packages\customtkinter;customtkinter" code_reviewer/main.py
```

O `.exe` será gerado em:
```
dist\CodeReviewer.exe
```

> Coloque o arquivo `.env` na mesma pasta que o `CodeReviewer.exe` para a chave ser carregada automaticamente.

> Se aparecer aviso do Windows Defender, clique em **"Mais informações" → "Executar assim mesmo"**.

---

## Como usar o app

1. Abra o app
2. A API Key é carregada do `.env` automaticamente (ou cole e clique em **💾 Salvar**)
3. Clique em **+ Adicionar Diff** e selecione seu arquivo `.diff` ou `.patch`
4. Clique em **Analisar ▶**
5. Navegue pelos problemas nas abas: **Bugs**, **Qualidade**, **Performance**

---

## Como gerar o arquivo .diff da sua branch

```cmd
git diff main...sua-branch > revisao.diff
```

Ou comparando com o commit anterior:

```cmd
git diff HEAD~1 > revisao.diff
```

---

## Modelo utilizado

`llama-3.3-70b-versatile` via Groq API.
