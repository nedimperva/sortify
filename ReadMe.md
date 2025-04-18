# Sortify

![Sortify Logo](https://api.placeholder.com/150/150)

**Sortify** is a modern, minimalist Windows application that automatically organizes your downloads by date and category. It runs quietly in the background, keeping your downloads folder tidy without any manual effort.

## ✨ Features

- **Automatic Sorting**: Files are instantly categorized by month and type
- **Custom Categories**: Define your own file categories and extensions
- **Modern UI**: Clean, native interface with light and dark mode support
- **System Tray**: Runs silently in the background with minimal resource usage
- **Interactive Charts**: Track your download habits with visual reports
- **Customizable**: Configure source/destination folders and sorting rules

## 📊 File Organization Structure

```
Downloads/
└── 2025/
    └── April/
        ├── Documents/
        ├── Images/
        ├── Videos/
        ├── Programs/
        └── Other/
```

## 🖼️ Screenshots

![Dashboard](https://api.placeholder.com/800/450)
*Dashboard with recent activity and statistics*

![Settings](https://api.placeholder.com/800/450)
*Customizable settings panel*

## 🚀 Installation

### Method 1: Installer (Recommended)
1. Download the latest installer from the [Releases](https://github.com/username/sortify/releases) page
2. Run the installer and follow the on-screen instructions
3. Launch Sortify from the Start menu

### Method 2: Manual Installation
1. Ensure you have Python 3.8+ installed
2. Clone this repository: `git clone https://github.com/username/sortify.git`
3. Navigate to the project directory: `cd sortify`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `python main.py`

## 🔧 Requirements

- Windows 10/11
- Python 3.8 or higher (for manual installation)
- PyQt6 (automatically installed with requirements.txt)
- Administrative privileges (for automatic startup configuration)

## 📝 Usage

1. **First Launch**: Configure your source and destination folders
2. **Categories**: Customize file categories and extensions if needed
3. **Background Operation**: Minimize to tray for silent operation
4. **Statistics**: View sorting statistics and activity in the dashboard
5. **Manual Sort**: Use the "Sort Now" button to manually trigger sorting

## ⚙️ Configuration

Sortify stores its configuration in `%USERPROFILE%\.sortify\config.json`. This file can be edited manually if needed, but it's recommended to use the Settings interface within the app.

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/username/sortify.git
cd sortify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
```

### Project Structure

```
sortify/
├── main.py                # Entry point
├── sorter/                # Backend sorting logic
│   ├── file_monitor.py    # File system monitoring
│   ├── file_sorter.py     # File sorting logic
│   ├── stats.py           # Statistics tracking
│   └── utils.py           # Utility functions
├── ui/                    # UI components
│   ├── main_window.py     # Main application window
│   ├── tray_icon.py       # System tray integration
│   └── resources/         # Icons and stylesheet
└── tests/                 # Test suite
```

### Running Tests

```bash
pytest tests/
```

### Building Executable

```bash
# Using PyInstaller
pyinstaller --onefile --windowed --icon=ui/resources/sortify_icon.png main.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - Modern UI framework
- [Watchdog](https://github.com/gorakhargosh/watchdog) - File system monitoring
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - Application packaging

---

## 📬 Contact

GitHub: [@YourUsername](https://github.com/yourusername)  
Twitter: [@YourTwitterHandle](https://twitter.com/yourtwitterhandle)

---

Made with ❤️ by [Your Name]
