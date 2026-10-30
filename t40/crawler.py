import logging
from . import model, fetcher, parser

def get_links(room: model.Room):
    links = []
    for rulecases in room.rules.values():
        for rulecase in rulecases:
            for command in rulecase.consequent:
                if command.varid == "opn":
                    links.append(command.arg)
    return links

def crawl(root_url: str):
    logging.info("Start crawl")
    adjacency_sparse_matrix = {}
    queue = [root_url]
    logging.info
    while queue:
        url = queue.pop(0)
        if url in adjacency_sparse_matrix: 
            logging.info("Already visited %s" % url)
            continue
        links = get_links(parser.parse(fetcher.fetch(url)))
        for link in links:
            logging.info("%s -> %s" % (url,link))
        adjacency_sparse_matrix[url] = links
        queue.extend(links)
    logging.info("Rooms visited: %d" % len(adjacency_sparse_matrix))
    return adjacency_sparse_matrix