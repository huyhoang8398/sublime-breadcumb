# Breadcrumb for Sublime Text

A clean and interactive **breadcrumb** that shows both the **file path** and the **current symbol hierarchy** at the top of the editor.

Powered by the LSP plugin for accurate, real-time symbol navigation.

![Breadcrumb Preview](./preview.png)  

## Features

- **Always visible** at the top of the view
- Real-time updates as you move the cursor
- Lightweight and fast
- Works great with Pyright, rust-analyzer, TypeScript, clangd, gopls, etc.

### Manual Installation

1. Download or clone this repository
2. Copy the folder into Sublime Text's `Packages` directory:
   - **Menu → Preferences → Browse Packages...**
3. Restart Sublime Text (or run `Package Control: Satisfy Dependencies`)

## Usage

- The breadcrumb appears automatically when you open a file with an active LSP session.
- Click on any part of the **file path** to open that folder.
- The display updates live on cursor movement.