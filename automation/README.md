# 🤖 Claude Auto-Approver

An intelligent automation tool that automatically responds to approval prompts when you're away from your computer for more than 5 minutes.

[한국어 문서 보기](README_KO.md)

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with default settings (5-minute timeout)
python auto_approver.py

# Run with custom settings
python auto_approver.py --timeout 300 --responses 2 yes y
```

## ✨ Features

- **🕐 Automatic Activity Detection**: Real-time monitoring of keyboard and mouse activity
- **⏰ Configurable Timeout**: Customizable wait time (default: 5 minutes)
- **⌨️ Auto Keyboard Input**: Automatically sends "2", "yes", etc. to approval prompts
- **🎯 Process Detection**: Automatically detects target applications (CMD, PyCharm, Terminal, etc.)
- **📊 Logging System**: Records all activities to a log file
- **🔧 Fully Customizable**: Configure responses, timeout, check interval, and more

## 📖 Usage

### Basic Usage

```bash
# Default settings
python auto_approver.py

# Custom timeout (10 minutes)
python auto_approver.py --timeout 600

# Custom responses
python auto_approver.py --responses 1 yes ok

# Target specific processes
python auto_approver.py --processes cmd python pycharm

# Debug mode
python auto_approver.py --debug
```

### Command-Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--timeout` | Wait time before auto-approval (seconds) | 300 (5 min) | `--timeout 600` |
| `--responses` | List of responses to send | `2 yes y` | `--responses 1 yes ok` |
| `--interval` | Activity check interval (seconds) | 10 | `--interval 5` |
| `--processes` | Target process names | `cmd pycharm terminal python claude` | `--processes cmd python` |
| `--debug` | Enable debug mode | False | `--debug` |

### Background Execution

```bash
# Run in background (Linux/Mac)
nohup python auto_approver.py &

# Check logs
tail -f auto_approver.log

# Stop background process
pkill -f auto_approver.py
```

## 🔍 How It Works

1. **Activity Monitoring**: Listens to keyboard and mouse events
2. **Inactivity Detection**: Calculates time since last activity
3. **Timeout Check**: Compares inactivity duration with configured timeout
4. **Process Verification**: Checks if target processes are running
5. **Auto-Approval**: Sends configured responses to approval prompts
6. **Logging**: Records all actions with timestamps

## 📋 Use Cases

### 1. During Long Tasks

```bash
# 1-hour timeout for lunch break
python auto_approver.py --timeout 3600 --responses yes
```

### 2. Overnight Automation

```bash
# 10-minute timeout, multiple responses
nohup python auto_approver.py --timeout 600 --responses 2 yes confirm &
```

### 3. PyCharm Development

```bash
# Target PyCharm only
python auto_approver.py --processes pycharm --responses 1 yes
```

### 4. Quick Testing

```bash
# 30-second timeout for testing
python auto_approver.py --timeout 30 --debug
```

## 🔒 Security Considerations

### ⚠️ Important Security Notes

1. **Auto-Approval Risks**
   - This program approves actions without user confirmation
   - Use caution with critical tasks or sensitive data
   - May approve unintended operations

2. **Recommended Environments**
   - ✅ Test environments
   - ✅ Development environments
   - ✅ Repetitive, safe tasks
   - ❌ Production environments
   - ❌ Critical system changes
   - ❌ Sensitive transactions

3. **Log Management**
   - All auto-approval activities are logged to `auto_approver.log`
   - Regularly review logs for unexpected behavior
   - Logs may contain sensitive information

4. **Access Control**
   - Limit physical/remote access to the running system
   - Prevent unauthorized use of the program

### 🛡️ Safe Usage Guidelines

```bash
# 1. Always monitor logs
tail -f auto_approver.log

# 2. Start with short timeouts
python auto_approver.py --timeout 60

# 3. Use debug mode to verify behavior
python auto_approver.py --debug

# 4. Target specific processes only
python auto_approver.py --processes my_safe_app

# 5. Test in safe environment first
python auto_approver.py --timeout 30 --debug
```

## 🐛 Troubleshooting

### Common Issues

#### 1. `pynput` Installation Error

```bash
pip install pynput

# Or with admin rights
sudo pip install pynput  # Linux/Mac
```

#### 2. Permission Error (Linux)

```bash
# Add user to input group
sudo usermod -a -G input $USER

# Log out and log back in
```

#### 3. `psutil` Not Found

```bash
pip install psutil
```

Note: The program works without `psutil`, but process detection will be limited.

#### 4. Auto-Approval Not Working

**Possible causes and solutions:**

1. **Target process not running**
   ```bash
   # Check running processes
   ps aux | grep -E 'cmd|pycharm|python'

   # Specify exact process name
   python auto_approver.py --processes actual_process_name
   ```

2. **Timeout too long**
   ```bash
   # Test with shorter timeout
   python auto_approver.py --timeout 30 --debug
   ```

3. **Continuous activity detection**
   ```bash
   # Check logs for activity status
   tail -f auto_approver.log
   ```

### Debug Mode

For persistent issues, enable debug mode:

```bash
python auto_approver.py --debug
```

Debug mode shows:
- Current inactivity duration
- Process detection status
- Key input attempts
- Error stack traces

## 📊 Log Example

```
2025-11-07 18:00:00 - INFO - ============================================================
2025-11-07 18:00:00 - INFO - Claude Auto-Approver Started
2025-11-07 18:00:00 - INFO - Inactivity timeout: 300 seconds (5.0 minutes)
2025-11-07 18:00:00 - INFO - Check interval: 10 seconds
2025-11-07 18:00:00 - INFO - Approval responses: 2, yes, y
2025-11-07 18:00:00 - INFO - Target processes: cmd, pycharm, terminal, python
2025-11-07 18:00:00 - INFO - ============================================================
2025-11-07 18:05:30 - INFO - User inactivity detected (330 seconds). Auto-approving...
2025-11-07 18:05:30 - INFO - Auto-approval attempt: '2'
2025-11-07 18:05:31 - INFO - Auto-approval completed (total: 1)
2025-11-07 18:05:32 - INFO - Auto-approval attempt: 'yes'
2025-11-07 18:05:33 - INFO - Auto-approval completed (total: 2)
```

## 🔧 Advanced Configuration

### Code Customization

Edit `auto_approver.py` for fine-grained control:

#### 1. Adjust Wait Time Between Responses

```python
# In send_approval method
time.sleep(0.5)  # Adjust this value (seconds)
```

#### 2. Change Log Level

```python
# In logging.basicConfig
level=logging.DEBUG  # More detailed logs
level=logging.WARNING  # Warnings and above only
```

## 📄 Requirements

- Python 3.7+
- pynput >= 1.7.6
- psutil >= 5.9.0

## 🤝 Contributing

Improvements and bug reports are always welcome!

### Ideas for Enhancement

- Add GUI interface
- Web dashboard for remote monitoring
- Smarter prompt detection
- Conditional approval rules

## 📄 License

This project is licensed under the MIT License.

---

## 📞 Support

If you have issues or questions:

1. Open an issue in the issue tracker
2. Attach log file (`auto_approver.log`)
3. Provide command used and environment info

**Happy Automating!** 🚀
