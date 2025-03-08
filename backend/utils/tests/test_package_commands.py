import re
import unittest
from unittest.mock import Mock, patch, MagicMock
import modal

from backend.utils.package_commands import handle_package_install_commands, parse_sandbox_process

class TestPackageCommands(unittest.TestCase):
    def setUp(self):
        self.mock_sandbox = Mock(spec=modal.Sandbox)
        self.mock_process = Mock()
        self.mock_process.stdout = ["Package installed successfully"]
        self.mock_process.stderr = []
        self.mock_sandbox.exec.return_value = self.mock_process
        
        # Mock parse_process function
        self.mock_parse_process = Mock(return_value=(["Package installed successfully"], 0))
        
    def test_handle_package_install_commands_npm_install_format(self):
        """Test npm install command in markdown code block format"""
        aider_result = """
        Here's the solution:
        
        ```bash
        npm install lodash-es @types/lodash-es
        ```
        
        Now you can use lodash in your project.
        """
        
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was called with the correct arguments
        self.mock_sandbox.exec.assert_called_once_with("pnpm", "add", "lodash-es", "@types/lodash-es")
        self.mock_parse_process.assert_called_once()
        
    def test_handle_package_install_commands_pnpm_add_format(self):
        """Test pnpm add command format at the beginning of a line"""
        aider_result = """
        Here's the solution:
        
        pnpm add react react-dom
        
        Now you can use React in your project.
        """
        
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was called with the correct arguments
        self.mock_sandbox.exec.assert_called_once_with("pnpm", "add", "react", "react-dom")
        self.mock_parse_process.assert_called_once()
        
    def test_handle_package_install_commands_with_flags(self):
        """Test package installation with flags"""
        aider_result = """
        Install as dev dependencies:
        
        ```
        npm install --save-dev jest @types/jest
        ```
        """
        
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was called with the correct arguments
        self.mock_sandbox.exec.assert_called_once_with("pnpm", "add", "--save-dev", "jest", "@types/jest")
        self.mock_parse_process.assert_called_once()
    
    def test_handle_package_install_commands_multiple_commands(self):
        """Test handling multiple package installation commands"""
        aider_result = """
        First, install the runtime dependencies:
        
        ```bash
        npm install express mongoose
        ```
        
        Then install the development dependencies:
        
        pnpm add --save-dev nodemon typescript
        """
        
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was called twice with different arguments
        self.assertEqual(self.mock_sandbox.exec.call_count, 2)
        self.mock_sandbox.exec.assert_any_call("pnpm", "add", "express", "mongoose")
        self.mock_sandbox.exec.assert_any_call("pnpm", "add", "--save-dev", "nodemon", "typescript")
        self.assertEqual(self.mock_parse_process.call_count, 2)
    
    def test_handle_package_install_commands_no_commands(self):
        """Test handling no package installation commands"""
        aider_result = """
        Here's the solution for your problem:
        
        ```javascript
        const add = (a, b) => a + b;
        ```
        
        You can use this function to add two numbers.
        """
        
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was not called
        self.mock_sandbox.exec.assert_not_called()
        self.mock_parse_process.assert_not_called()
    
    def test_handle_package_install_commands_empty_packages(self):
        """Test handling package installation command with no packages"""
        aider_result = """
        ```bash
        npm install 
        ```
        """
        
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was not called because no packages were specified
        self.mock_sandbox.exec.assert_not_called()
        self.mock_parse_process.assert_not_called()
    
    def test_handle_package_install_commands_sandbox_none(self):
        """Test handling None sandbox"""
        aider_result = """
        ```bash
        npm install lodash
        ```
        """
        
        # This should not raise an exception
        handle_package_install_commands(aider_result, None, self.mock_parse_process)
        
        # No assertions needed, we just want to make sure it doesn't crash
    
    def test_installation_error(self):
        """Test handling installation error"""
        aider_result = """
        ```bash
        npm install non-existent-package
        ```
        """
        
        # Mock an error during installation
        self.mock_sandbox.exec.side_effect = Exception("Installation failed")
        
        # This should not raise an exception
        handle_package_install_commands(aider_result, self.mock_sandbox, self.mock_parse_process)
        
        # Verify sandbox.exec was called
        self.mock_sandbox.exec.assert_called_once()
        # We don't call parse_process because exec raised an exception
        self.mock_parse_process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
