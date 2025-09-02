# Izza Email Test Web Application

This is a FastAPI web application for testing purposes.

## Features

- Displays a table with columns: '시도', '시군구', '유형', '단지명', '고시일자', '고시번호', '고시명', 'pdf'.
- Manually updatable table via an admin page.
- PDF download support.

## Project Structure

```
.
├── data
│   ├── data.json
│   └── pdfs
├── main.py
├── static
│   └── style.css
└── templates
    ├── admin.html
    └── index.html
```

## Setup and Run

1.  **Install dependencies:**

    ```bash
    pip install fastapi uvicorn jinja2 python-multipart
    ```

2.  **Run the application:**

    ```bash
    uvicorn main:app --reload
    ```

3.  **Access the application:**

    -   Main page: [http://127.0.0.1:8000](http://127.0.0.1:8000)
    -   Admin page: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

## Notes

-   The application stores data in `data/data.json`.
-   Uploaded PDF files are stored in the `data/pdfs` directory.
-   Make sure to create the `data/pdfs` directory if it doesn't exist.