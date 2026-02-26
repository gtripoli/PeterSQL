# PeterSQL Themes

This directory contains theme files for PeterSQL. Each theme defines colors for the editor and autocomplete components, with support for both dark and light modes.

## Theme Structure

Each theme is a YAML file with the following structure:

```yaml
name: Theme Name
version: 1.0

editor:
  dark:
    # Colors for dark mode
    background: auto  # 'auto' uses system color
    foreground: auto
    keyword: '#569cd6'
    string: '#ce9178'
    # ... more colors
  
  light:
    # Colors for light mode
    background: auto
    foreground: auto
    keyword: '#0000ff'
    # ... more colors

autocomplete:
  dark:
    keyword: '#569cd6'
    function: '#dcdcaa'
    table: '#4ec9b0'
    column: '#9cdcfe'
  
  light:
    keyword: '#0000ff'
    function: '#800080'
    table: '#008000'
    column: '#000000'
```

## Available Colors

### Editor Colors
- `background` - Editor background
- `foreground` - Default text color
- `line_number_background` - Line number margin background
- `line_number_foreground` - Line number text color
- `keyword` - SQL keywords (SELECT, FROM, etc.)
- `string` - String literals
- `comment` - Comments
- `number` - Numeric literals
- `operator` - Operators (+, -, *, etc.)
- `property` - JSON properties
- `error` - Error highlighting
- `uri` - URI/URL highlighting
- `reference` - Reference highlighting
- `document` - Document markers

### Autocomplete Colors
- `keyword` - SQL keywords
- `function` - SQL functions
- `table` - Table names
- `column` - Column names

## Using 'auto' Color

Set a color to `auto` to use the system color. This is useful for background and foreground colors to ensure the editor adapts to the system theme.

## Creating a New Theme

1. Create a new YAML file in this directory (e.g., `mytheme.yml`)
2. Copy the structure from `petersql.yml`
3. Customize the colors
4. Update `settings.yml` to use your theme:
   ```yaml
   theme:
     current: mytheme
   ```

## Default Theme

The default theme is `petersql.yml`, which provides VS Code-like colors for both dark and light modes.
