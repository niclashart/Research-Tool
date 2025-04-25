from datetime import datetime

def format_arxiv_citation(paper_data, citation_style="apa"):
    """
    Generate formatted citation for arXiv papers
    Args:
        paper_data: Dictionary containing paper data
        citation_style: "apa", "mla", "chicago" or "bibtex"
    Returns:
        Formatted citation string
    """
    if citation_style.lower() == "apa":
        return generate_apa_citation(paper_data)
    elif citation_style.lower() == "mla":
        return generate_mla_citation(paper_data)
    elif citation_style.lower() == "chicago":
        return generate_chicago_citation(paper_data)
    elif citation_style.lower() == "bibtex":
        return generate_bibtex_citation(paper_data)
    else:
        return generate_apa_citation(paper_data)

def generate_apa_citation(paper):
    """Generate APA style citation"""
    # Format authors
    authors = paper.get('authors', [])
    if isinstance(authors, str):
        authors = [authors]
    
    if len(authors) == 0:
        author_text = "Anonymous"
    elif len(authors) == 1:
        author_text = authors[0]
    elif len(authors) == 2:
        author_text = f"{authors[0]} & {authors[1]}"
    else:
        author_text = f"{authors[0]} et al."
    
    # Format year
    published = paper.get('published', datetime.now())
    if isinstance(published, str):
        try:
            year = published.split('-')[0]
        except:
            year = str(datetime.now().year)
    else:
        year = str(published.year)
    
    # Format title
    title = paper.get('title', '').strip()
    if not title.endswith('.'):
        title += '.'
    
    # Get arXiv ID
    link = paper.get('link', '')
    arxiv_id = link.split('/')[-1].replace('.pdf', '')
    
    # Format citation
    citation = f"{author_text} ({year}). {title} arXiv preprint arXiv:{arxiv_id}"
    
    return citation

def generate_mla_citation(paper):
    """Generate MLA style citation"""
    # Format authors
    authors = paper.get('authors', [])
    if isinstance(authors, str):
        authors = [authors]
    
    if len(authors) == 0:
        author_text = "Anonymous"
    elif len(authors) == 1:
        last_first = authors[0].split()
        if len(last_first) > 1:
            author_text = f"{last_first[-1]}, {' '.join(last_first[:-1])}"
        else:
            author_text = last_first[0]
    else:
        last_first = authors[0].split()
        if len(last_first) > 1:
            author_text = f"{last_first[-1]}, {' '.join(last_first[:-1])}, et al"
        else:
            author_text = f"{last_first[0]}, et al"
    
    # Format title
    title = f"\"{paper.get('title', '').strip()}\""
    
    # Format date
    published = paper.get('published', datetime.now())
    if isinstance(published, str):
        try:
            date_parts = published.split('-')
            date = f"{date_parts[0]}"
        except:
            date = str(datetime.now().year)
    else:
        date = str(published.year)
    
    # Get arXiv ID
    link = paper.get('link', '')
    arxiv_id = link.split('/')[-1].replace('.pdf', '')
    
    # Format citation
    citation = f"{author_text}. {title}. arXiv:{arxiv_id}, {date}."
    
    return citation

def generate_chicago_citation(paper):
    """Generate Chicago style citation"""
    # Format authors
    authors = paper.get('authors', [])
    if isinstance(authors, str):
        authors = [authors]
    
    if len(authors) == 0:
        author_text = "Anonymous"
    elif len(authors) == 1:
        author_text = authors[0]
    else:
        author_text = f"{authors[0]}, and {authors[1]}" if len(authors) == 2 else f"{authors[0]} et al."
    
    # Format title
    title = f"\"{paper.get('title', '').strip()}\""
    
    # Format date
    published = paper.get('published', datetime.now())
    if isinstance(published, str):
        try:
            date = published.split('-')[0]
        except:
            date = str(datetime.now().year)
    else:
        date = str(published.year)
    
    # Get arXiv ID
    link = paper.get('link', '')
    arxiv_id = link.split('/')[-1].replace('.pdf', '')
    
    # Format citation
    citation = f"{author_text}. {title} arXiv:{arxiv_id} ({date})."
    
    return citation

def generate_bibtex_citation(paper):
    """Generate BibTeX citation"""
    # Get arXiv ID
    link = paper.get('link', '')
    arxiv_id = link.split('/')[-1].replace('.pdf', '')
    
    # Format authors for BibTeX
    authors = paper.get('authors', [])
    if isinstance(authors, str):
        authors = [authors]
    
    if len(authors) == 0:
        author_text = "Anonymous"
    else:
        author_text = " and ".join(authors)
    
    # Format title
    title = paper.get('title', '').strip()
    
    # Format date
    published = paper.get('published', datetime.now())
    if isinstance(published, str):
        try:
            year = published.split('-')[0]
        except:
            year = str(datetime.now().year)
    else:
        year = str(published.year)
    
    # Create BibTeX entry
    bibtex = (
        f"@article{{{arxiv_id},\n"
        f"  author = {{{author_text}}},\n"
        f"  title = {{{title}}},\n"
        f"  journal = {{arXiv preprint arXiv:{arxiv_id}}},\n"
        f"  year = {{{year}}},\n"
        f"  url = {{https://arxiv.org/abs/{arxiv_id}}}\n"
        f"}}"
    )
    
    return bibtex