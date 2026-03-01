# IntelliJ MCP Capabilities Report

Date: 2026-02-26
Workspace: /Users/velocityworks/IdeaProjects/wet-donkey

## Connection Status

- IntelliJ MCP server connection: active
- Handshake status: successful
- Verified call: `get_project_modules` returned module `wet-donkey` (`JAVA_MODULE`)
- Note: `resources/list` and `resources/templates/list` are not implemented by this server (`-32601`) and are not required for tool usage

## IntelliJ MCP Functionality Exposed

### Project and workspace discovery
- `get_project_modules`: list project modules
- `get_project_dependencies`: list dependencies
- `get_repositories`: list VCS roots
- `get_run_configurations`: list run configurations
- `get_all_open_file_paths`: list active/open editors
- `list_directory_tree`: inspect project directory tree

### File content and diagnostics
- `get_file_text_by_path`: read file contents
- `get_file_problems`: run IntelliJ inspections for a file (errors/warnings)
- `get_symbol_info`: inspect symbol/docs at a specific line+column

### Search and navigation
- `find_files_by_name_keyword`: fast filename keyword search
- `find_files_by_glob`: glob-based file discovery
- `search_in_files_by_text`: indexed text search across files
- `search_in_files_by_regex`: regex search across files
- `open_file_in_editor`: open file in IDE editor

### Editing and refactoring
- `create_new_file`: create file (with optional content)
- `replace_text_in_file`: targeted in-file replacement
- `rename_refactoring`: semantic symbol rename across references
- `reformat_file`: apply IntelliJ formatter

### Build and execution
- `build_project`: build/rebuild project or selected files
- `execute_run_configuration`: run an IDE run configuration
- `execute_terminal_command`: run commands in IDE terminal
- `runNotebookCell`: run a notebook cell or whole notebook

### IDE permission mediation
- `permission_prompt`: trigger IDE-side permission prompts when needed

## Additional Non-IntelliJ Capabilities Available In This Session

- Shell execution via PTY (`exec_command`, `write_stdin`)
- Multi-tool parallel execution orchestration (`multi_tool_use.parallel`)
- Web lookup tooling (search/open/find/screenshot/weather/finance/time/sports)
- MCP resource/template listing and reads for configured MCP servers

## Current Practical Use Cases You Can Ask For

- "Run IntelliJ inspections on file X and summarize only errors."
- "Find all references to symbol Y and rename it safely."
- "Build the project and report compile failures with file/line pointers."
- "Run run configuration Z and summarize runtime output."
- "Search this project for regex pattern P and show exact hit locations."
