# Try it out!
[https://latexsymbolsearch.herokuapp.com](https://latexsymbolsearch.herokuapp.com)

# Description
This is a search engine for LaTeX mathematical symbols. It indexes the tables of mathematical symbols in [Wikipedia's](http://en.wikipedia.org/wiki/List_of_mathematical_symbols) and [Wikibooks'](http://en.wikibooks.org/wiki/LaTeX/Mathematics#List_of_Mathematical_Symbols) list of mathematical symbols pages.

# Data
There are some comprehensive LaTeX symbol lists, but all of the ones I found only contained the symbol and its command. This is not very useful for a search engine as the user can only find the symbol if the correct command is entered, and if the user already knows the command, what is the point of using a search engine?

Therefore, I used Wikipedia's web page [{list of mathematical symbols}](http://en.wikipedia.org/wiki/List_of_mathematical_symbols) as the main data source, as it includes the following attributes of each symbol:

* name
* read as
* category
* explanation
* examples

Fortunately, each equation image also included the LaTeX command used to generate said equation, which be found in its HTML image attribute: `<img alt="\command">`.

Using this information along with the HTML parser BeautifulSoup, we can combine these so that when the user hovers over the image, the equation formula is shown. There is a growing resistance for the use of hover in an age that is more and more geared towards mobile platforms. However, I think that most of the users of this service will be using it through a computer or laptop since document writing (especially scientific documents which LaTeX is aimed at) is most commonly done with a physical keyboard and mouse. Also, this was the only satisfactory way I could think of to display the source code, as displaying it besides the equations makes the whole presentation look very messy.

However, Wikpedia's list is not comprehensive and therefore another source is needed. There is a comprehensive LaTeX symbols list in pdf form, but a pdf is not easy to parse. Also, most of these symbols are taken from different packages and I wanted to stick to the more commonly used ones. Therefore [Wikibooks' list of mathematical symbols](http://en.wikibooks.org/wiki/LaTeX/Mathematics#List_of_Mathematical_Symbols), which lists all of the pre-defined mathematical symbols from the TeX package is also used to complement the symbol list. As stated before, these symbols only contain information about their commands and nothing else.

# Indexing
Each row in the tables of symbols is treated as one document. An example would be the the row representing multiplcation in [Wikipedia's mathematical symbols list](http://en.wikipedia.org/wiki/List_of_mathematical_symbols). In this example, it can be seen that one concept (multiplication or dot product in this case) may be represented by multiple symbols (\times and \cdot here). The indexed fields of each document is then:

* TeX Command
* Keyword: the words in the column: name, read as, category.
* Content: the words in the column explanation and examples.

For [Wikibooks' mathematical symbols list](http://en.wikibooks.org/wiki/LaTeX/Mathematics#List_of_Mathematical_Symbols), these symbols are only indexed by their commands as more information is not provided.

# Querying
The search engine supports fuzzy search with a maximum edit distance of 3. As an example, the query "esplon" still returns the results for `"epsilon": \epsilon and \varepsilon.

As the content (explanation and examples) are indexed by the search engine, one can also query for the content of a symbol. As an example, the query "the set of real numbers" returns the symbols \mathbb{R} and \mathbf{R}.

# Ranking
[Whoosh](https://pypi.python.org/pypi/Whoosh/), a Python based search engine, is used for this project. It uses the ranking algorithm [Okapi BM25F](http://en.wikipedia.org/wiki/Okapi_BM25), which is a probabilistic relevance model, based on the principle of document generation:

P(Q,D | R) = P(D | Q,R) P(Q | R)

which intuitively can be thought of as the probability of a document being generated by this query.

BM25 is based on a bag-of-words approach. The score of a document $D$ given a query $Q$ which contains the words $q_1, ..., q_n$ is given by:

\begin{equation} \label{eq:bm25}
 \text{score}(D,Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{\text{avgdl}})}
\end{equation}

where $f(q_i, D)$ is $q_i$'s term frequency in the document $D$, $|D|$ is the length of the document $D$ in words, and avgdl is the average document length in the text collection from which documents are drawn. $k_1$ and $b$ are free parameters.

The system then performs multiple searches with the same query, but using different types of searches and then combining the search results in the following priority:

* Exact match
	* Matches the exact query with the fields: commands and keywords
* Or match
	* Exact match with each word in the query (i.e. OR matching) with the fields: commands and keywords
* Fuzzy: commands
	* Fuzzy search (max edit distance of 3) using each word in the query (i.e. OR matching) with the field: commands
* Fuzzy: keywords
	* Fuzzy search (max edit distance of 3) using each word in the query (i.e. OR matching) with the field: keywords
* Fuzzy: content
	* Fuzzy search (max edit distance of 3) using each word in the query (i.e. OR matching) with the field: content

This is achieved through the Whoosh's function `upgrade_and_extend()` which combines different search results sets and ranks results that occur in both sets higher.

```Python
% Get different search results
exact_parser = get_exact_parser(
    fields=[COMMANDS, KEYWORDS])
exact_results = get_results(exact_parser(user_query))

or_parser = get_or_parser(
    fields=[COMMANDS, KEYWORDS])
or_results = get_results(or_parser(user_query))

fuzzy_commands_parser = get_fuzzy_commands_parser(
    fields=[COMMANDS])
fuzzy_commands_results = get_results(fuzzy_commands_parser(user_query))

fuzzy_keywords_parser = get_fuzzy_keywords_parser(
    fields=[KEYWORDS])
fuzzy_keywords_results = get_results(fuzzy_keywords_parser(user_query))

fuzzy_content_parser = get_fuzzy_content_parser(
    fields=[CONTENT])
fuzzy_content_results = get_results(fuzzy_content_parser(user_query))

% Combine these search results
% from lowest to highest priority
fuzzy_keywords_results.upgrade_and_extend(fuzzy_content_results)
fuzzy_commands_results.upgrade_and_extend(fuzzy_keywords_results)
or_results.upgrade_and_extend(fuzzy_commands_results)
exact_results.upgrade_and_extend(or_results)
```

# Todo
* Separation of content and style: at the moment each table row is stored along with all the html tags, should extract and store only content. Very very ugly.
* Collapsed and expandable table rows: first show only symbol and command, then on click expand explanation and examples.
* AJAX for search as you type
* Highlight matched terms (Whoosh built in feature)
* Search suggestion: "Did you mean ...?" (Whoosh built in feature)
