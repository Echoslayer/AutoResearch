# AutoResearch

AutoResearch is an AI-powered system designed to assist in the generation and structuring of research papers. It leverages Django and various AI technologies to streamline the research writing process.

## Features

- Generate rough outlines for research papers
- Merge multiple outlines into a cohesive structure
- Create detailed subsection outlines
- Edit and refine final outlines
- Check and improve subsection outlines
- Generate subsection content with proper citations
- Verify and check citations

## Technologies Used

- Django
- Django REST Framework
- OpenAI API
- Langchain
- drf-yasg (for API documentation)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/ChiaXinLiang/AutoResearch.git
   cd AutoResearch
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Start the development server:
   ```
   python manage.py runserver
   ```

## API Documentation

The API documentation is available through Swagger UI. After starting the server, visit:

http://localhost:8000/swagger/

You can explore and test the various API endpoints for research paper assistance.

## Usage

The main functionality is exposed through various API endpoints. You can use these endpoints to generate different types of content for various stages of the research paper writing process.

Example usage with curl:
