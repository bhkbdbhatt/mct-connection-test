# DHL MCT Automation Testing Project

This project contains automated tests for DHL MCT (Multi-Channel Technology) using Python and Pytest.

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Git (for version control)

## Local Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-folder>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   
   # For Windows
   .venv\Scripts\activate
   
   # For macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

### Running Individual Test Cases

There are several ways to run specific test cases:

1. **Running by Test Name**

To run a specific test case by its name:

```bash
pytest -v -k "test_name"
```

Example:
```bash
pytest -v -k "test_customer_service_utterance"
```

2. **Running by Test Marker**

To run tests with specific markers (defined in pytest.ini):

```bash
pytest -v -m "checkpoint"
```

Example:
```bash
pytest -v -m "checkpoint" test_cases_screen_recorder.py
```

3. **Running from Specific File**

To run a specific test from a particular file:

```bash
pytest test_cases_screen_recorder.py -v -k "test_customer_service_utterance"
```

4. **Running with Additional Options**

Combine with other pytest options:

```bash
pytest -v -k "test_customer_service_utterance" --html=report.html
```
5. **Running with particular function**
```cmd
pytest test_cases_screen_recorder.py::test_dhl_automation_PL_valid_account_number -v
```
### Running All Tests

To run all test cases:

```bash
pytest -v
```

### Running Tests with Screen Recording

The project includes screen recording functionality. To run tests with screen recording:

```bash
pytest test_cases_screen_recorder.py -v
```

Recorded videos will be saved in the `videos/` directory.

### Configuring Country for Tests

To change the country for screen recording tests:

1. Open `test_cases_screen_recorder.py`
2. Locate the `setup_driver` fixture (around line 132)
3. Modify the `country_code` variable with the desired country code:
   ```python
   country_code = 'zm'  # Change 'zm' to your desired country code
   ```

Available country codes can be found in:
- `country_config.json`: For European and African countries
- `country_config_ap.json`: For Asia Pacific countries
- `country_config_am.json`: For American countries

Each country configuration includes:
- Username and password
- Supported language codes
- Site reference (for specific countries)

## Generating Test Reports

### HTML Report

To generate an HTML report:

```bash
pytest --html=report.html
```

## Project Structure

- `test_cases_for_chat_transfer.py`: Main test cases for chat transfer functionality
- `test_cases_screen_recorder.py`: Test cases with screen recording
- `locators.py`: Page element locators
- `config.py`: Configuration settings
- `country_config*.json`: Country-specific configurations
- `util_functions.py`: Utility functions
- `requirements.txt`: Project dependencies

## Common Issues and Troubleshooting

1. **Virtual Environment Issues**
   - Ensure virtual environment is activated
   - Reinstall dependencies if needed

2. **Test Execution Failures**
   - Check network connectivity
   - Verify credentials in config files
   - Ensure all dependencies are installed correctly

3. **Country Configuration Issues**
   - Verify the country code exists in the appropriate config file
   - Check if the required language codes are available
   - Ensure the site reference is correct (if applicable)

## Additional Notes

- Keep the virtual environment activated while running tests
- Ensure proper internet connectivity for tests
- Check the videos directory for recorded test sessions
- Review test reports in the project root directory

## Contributing

1. Create a new branch for your changes
2. Make your changes and test them
3. Submit a pull request

## Support

For any issues or questions, please contact the project maintainers.
