#!/usr/bin/env python3
"""Clean Obsidian-specific syntax from markdown notes for GitHub Pages display."""

import re, sys, os
from pathlib import Path

def clean_obsidian(text):
    """Remove Obsidian-specific syntax, keep standard markdown."""
    
    # 1. Remove YAML frontmatter (between --- at the very start)
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            text = text[end + 3:].lstrip('\n')
    
    # 2. Convert Obsidian callouts to standard markdown
    # Pattern: > [!type] or > [!type]- with optional title
    # We strip the [!type] tag but keep the content
    lines = text.split('\n')
    cleaned = []
    in_callout = False
    callout_indent = ''
    
    for line in lines:
        # Match > [!TYPE] or > [!TYPE]-
        callout_match = re.match(r'^((> ?\s*)*)\[!(\w+)\][+-]?\s*(.*)', line.strip())
        
        if line.strip().startswith('> [!') or line.strip().startswith('>[!'):
            in_callout = True
            callout_indent = re.match(r'^(> ?\s*)', line)
            callout_indent = callout_indent.group(1) if callout_indent else ''
            
            # Extract the content after the callout tag
            content = re.sub(r'\[!\w+\][+-]?\s*', '', line.strip())
            if content.strip():
                # Replace with standard blockquote
                cleaned_line = re.sub(r'^> ', '', content)
                cleaned.append('> ' + cleaned_line)
            else:
                cleaned.append('')
            continue
        
        if in_callout and line.strip() and line.startswith('>'):
            if line.strip() == '>':
                cleaned.append('')
                continue
            # Continue the blockquote - just remove the [! ] wrapper vestiges
            cleaned.append(line)
            continue
        elif in_callout and (not line.strip() or not line.startswith('>')):
            in_callout = False
            cleaned.append(line)
            continue
        
        cleaned.append(line)
    
    text = '\n'.join(cleaned)
    
    # 3. Remove collapsible header remnants (lines like "> ###" after callout removal)
    # Nothing extra needed - handled above
    
    # 4. Convert wiki-links [[page]] → page
    text = re.sub(r'\[\[([^\]]+?)(?:\|[^\]]+)?\]\]', r'\1', text)
    
    # 5. Clean up double blank lines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 6. Remove trailing whitespace
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    
    # 7. Ensure single trailing newline
    text = text.rstrip() + '\n'
    
    return text

def clean_file(filepath):
    """Clean a single markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    cleaned = clean_obsidian(text)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_dir():
            for md_file in sorted(target.glob('*.md')):
                if clean_file(md_file):
                    print(f'✅ {md_file.name}')
        else:
            clean_file(target)
            print(f'✅ {target.name}')
    else:
        # Clean all .md in notes/
        notes_dir = Path(__file__).parent / 'notes'
        for md_file in sorted(notes_dir.glob('*.md')):
            if clean_file(md_file):
                print(f'✅ {md_file.name}')
