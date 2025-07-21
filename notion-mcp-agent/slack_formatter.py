"""
Slack Markdown Formatter
Converts standard markdown to Slack's mrkdwn format
Reference: https://api.slack.com/reference/surfaces/formatting
"""
import re
from typing import Dict, List

class SlackFormatter:
    """Convert standard markdown to Slack mrkdwn format"""
    
    def __init__(self):
        # Regex patterns for markdown conversion
        # Order matters - process bold before italic to avoid conflicts
        self.patterns = [
            # Headers - convert to bold (Slack doesn't have native headers)  
            (r'^### (.*?)$', r'*\1*'),  # H3
            (r'^## (.*?)$', r'*\1*'),   # H2  
            (r'^# (.*?)$', r'*\1*'),    # H1
            
            # Bold - ** to * (Slack uses single asterisk for bold)
            (r'\*\*(.*?)\*\*', r'*\1*'),
            
            # Italic - * to _ (single asterisk to underscore for italic)
            (r'(?<!\*)\*([^*]+?)\*(?!\*)', r'_\1_'),
            
            # Strikethrough - ~~ to ~
            (r'~~(.*?)~~', r'~\1~'),
            
            # Inline code - ` to ` (same in Slack)
            (r'`([^`]+?)`', r'`\1`'),
            
            # Links - [text](url) to <url|text>
            (r'\[([^\]]+?)\]\(([^)]+?)\)', r'<\2|\1>'),
            
            # Unordered lists - convert to Slack bullet format
            (r'^[\s]*[-\*\+] (.*?)$', r'• \1'),
            
            # Ordered lists - keep numbers but clean formatting
            (r'^[\s]*(\d+)\. (.*?)$', r'\1. \2'),
            
            # Blockquotes - > to >
            (r'^> (.*?)$', r'> \1'),
        ]
    
    def convert_code_blocks(self, text: str) -> str:
        """Convert code blocks to Slack format"""
        # Multi-line code blocks ```lang to ```
        text = re.sub(r'```[\w]*\n(.*?)\n```', r'```\1```', text, flags=re.DOTALL)
        return text
    
    def convert_lists(self, text: str) -> str:
        """Better list conversion with proper spacing"""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # Unordered lists
            if re.match(r'^[\s]*[-\*\+] ', line):
                # Replace with bullet and maintain indentation
                indent = len(line) - len(line.lstrip())
                content = re.sub(r'^[\s]*[-\*\+] ', '', line)
                result.append(' ' * indent + '• ' + content)
            
            # Ordered lists  
            elif re.match(r'^[\s]*\d+\. ', line):
                result.append(line)
            
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def convert_to_slack_mrkdwn(self, markdown_text: str) -> str:
        """
        Convert standard markdown to Slack mrkdwn format
        
        Args:
            markdown_text: Standard markdown text
            
        Returns:
            Slack mrkdwn formatted text
        """
        if not markdown_text:
            return ""
        
        # Start with the original text
        text = markdown_text
        
        # Handle code blocks first (to avoid interfering with other patterns)
        text = self.convert_code_blocks(text)
        
        # Process each line separately for proper formatting
        lines = text.split('\n')
        converted_lines = []
        
        for line in lines:
            converted_line = line
            
            # Handle headers first (line-specific) 
            if re.match(r'^### ', line):
                converted_line = re.sub(r'^### (.*?)$', r'*\1*', converted_line)
            elif re.match(r'^## ', line):
                converted_line = re.sub(r'^## (.*?)$', r'*\1*', converted_line)
            elif re.match(r'^# ', line):
                converted_line = re.sub(r'^# (.*?)$', r'*\1*', converted_line)
            else:
                # Apply inline formatting patterns in order
                # Process bold first, then italic to avoid conflicts
                # Use temporary markers to prevent conflicts
                converted_line = re.sub(r'\*\*(.*?)\*\*', r'__BOLD_START__\1__BOLD_END__', converted_line)  # Bold: ** to temp marker
                converted_line = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'_\1_', converted_line)  # Italic: * to _
                # Convert temp markers back to Slack bold format
                converted_line = converted_line.replace('__BOLD_START__', '*').replace('__BOLD_END__', '*')
                converted_line = re.sub(r'~~(.*?)~~', r'~\1~', converted_line)  # Strikethrough
                converted_line = re.sub(r'`([^`]+?)`', r'`\1`', converted_line)  # Code (no change)
                converted_line = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<\2|\1>', converted_line)  # Links
                converted_line = re.sub(r'^[\s]*[-\*\+] (.*?)$', r'• \1', converted_line)  # Lists
                converted_line = re.sub(r'^[\s]*(\d+)\. (.*?)$', r'\1. \2', converted_line)  # Ordered lists  
                converted_line = re.sub(r'^> (.*?)$', r'> \1', converted_line)  # Blockquotes
            
            converted_lines.append(converted_line)
        
        # Rejoin lines
        text = '\n'.join(converted_lines)
        
        # Handle lists with better formatting
        text = self.convert_lists(text)
        
        # Clean up multiple newlines (Slack handles spacing differently)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def create_slack_blocks(self, text: str, max_block_length: int = 3000) -> List[Dict]:
        """
        Convert text to Slack blocks format for better rendering
        
        Args:
            text: Formatted text
            max_block_length: Maximum length per block
            
        Returns:
            List of Slack block elements
        """
        blocks = []
        
        # If text is short enough, create a single block
        if len(text) <= max_block_length:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            })
        else:
            # Split long text into multiple blocks
            paragraphs = text.split('\n\n')
            current_block = ""
            
            for paragraph in paragraphs:
                # If adding this paragraph would exceed the limit, start a new block
                if len(current_block + paragraph) > max_block_length and current_block:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn", 
                            "text": current_block.strip()
                        }
                    })
                    current_block = paragraph + '\n\n'
                else:
                    current_block += paragraph + '\n\n'
            
            # Add the final block if there's remaining content
            if current_block.strip():
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": current_block.strip()
                    }
                })
        
        return blocks

# Global instance for easy use
slack_formatter = SlackFormatter()

# Convenience functions
def to_slack_mrkdwn(markdown_text: str) -> str:
    """Convert markdown to Slack mrkdwn format"""
    return slack_formatter.convert_to_slack_mrkdwn(markdown_text)

def to_slack_blocks(text: str) -> List[Dict]:
    """Convert text to Slack blocks"""
    formatted_text = slack_formatter.convert_to_slack_mrkdwn(text)
    return slack_formatter.create_slack_blocks(formatted_text)

# Example usage and tests
if __name__ == "__main__":
    test_markdown = """
# Main Header
This is a paragraph with **bold text** and *italic text* and `inline code`.

## Subheader
Here's a [link](https://example.com) and some ~~strikethrough~~ text.

### Features:
- Bullet point one
- Bullet point two with **bold**
- Bullet point three

### Numbered list:
1. First item
2. Second item with `code`
3. Third item

> This is a blockquote

```python
def hello():
    return "Hello World"
```

More text after code block.
"""
    
    print("Original Markdown:")
    print(test_markdown)
    print("\n" + "="*50 + "\n")
    
    formatted = to_slack_mrkdwn(test_markdown)
    print("Slack mrkdwn:")
    print(formatted)
    print("\n" + "="*50 + "\n")
    
    blocks = to_slack_blocks(test_markdown)
    print("Slack Blocks:")
    for i, block in enumerate(blocks):
        print(f"Block {i+1}:")
        print(block)
        print()