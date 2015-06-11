from flask import Flask, request, render_template

import os
from whoosh.index import open_dir

from src import indexer, global_constants

INDEX_DIR = os.path.join(".", "index")

app = Flask(__name__)
app.debug = True


@app.route('/', methods=['GET'])
def home():
    user_query = request.args.get('query', '').strip()
    if user_query:
        print user_query
        schema = indexer.get_schema()
        ix = open_dir(INDEX_DIR)

        with ix.searcher() as searcher:
            exact_parser = indexer.get_exact_qparser(
                [global_constants.COMMANDS, global_constants.KEYWORDS], schema)
            exact_query = exact_parser.parse(user_query)
            exact_results = searcher.search(exact_query, limit=5)

            exact_or_parser = indexer.get_exact_or_qparser(
                [global_constants.COMMANDS, global_constants.KEYWORDS], schema)
            exact_or_query = exact_or_parser.parse(user_query)
            exact_or_results = searcher.search(exact_or_query, limit=5)

            cmd_parser = indexer.get_fuzzy_qparser([global_constants.COMMANDS], schema)
            cmd_query = cmd_parser.parse(user_query)
            cmd_results = searcher.search(cmd_query, limit=5)

            keyword_parser = indexer.get_fuzzy_qparser([global_constants.KEYWORDS], schema)
            keyword_query = keyword_parser.parse(user_query)
            keyword_results = searcher.search(keyword_query, limit=5)

            content_parser = indexer.get_fuzzy_qparser([global_constants.CONTENT], schema)
            content_query = content_parser.parse(user_query)
            content_results = searcher.search(content_query, limit=10)

            keyword_results.upgrade_and_extend(content_results)
            cmd_results.upgrade_and_extend(keyword_results)
            exact_or_results.upgrade_and_extend(cmd_results)
            exact_results.upgrade_and_extend(exact_or_results)

            ordered_results_set = [
                exact_results,
                exact_or_results,
                cmd_results,
                keyword_results,
                content_results
            ]

            results = exact_results
            for result_set in ordered_results_set:
                if len(result_set) > 0:
                    results = result_set
                    break

            html_results = [r[global_constants.HTML] for r in results]

            return render_template(
                "search_home_query.html", table_rows=html_results, query=user_query)
    else:
        return render_template("search_home.html")

if __name__ == "__main__":
    app.run()
