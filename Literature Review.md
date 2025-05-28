# Literature Review

Through literature review, we aim to answer the following questions:

1. Which models to try
2. Which metrics to use in evaluation
3. How to summarize documents longer than a model’s max input
4. Which available datasets to use, or how to create a dataset from OBD

## Reading List

1. [A Comprehensive Survey on Process-Oriented Automatic Text Summarization with Exploration of LLM-Based Methods](https://arxiv.org/abs/2403.02901)

   This paper is a comprehensive survey on Automatic Text Summarization (ATS), focusing particularly on the latest
   advancements driven by Large Language Models (LLMs). It traces the historical evolution of ATS from early statistical
   methods to modern deep learning techniques, highlighting the paradigm shift introduced by LLMs with their superior
   generative and learning capabilities. The authors review existing ATS methods and introduce a novel retrieval
   algorithm for efficiently collecting research papers, aiming to provide an up-to-date overview of the field and
   explore future directions for LLM-based summarization.

    - Datasets:
        - [Gigaword](https://catalog.ldc.upenn.edu/LDC2011T07): With nearly 10 million English news documents and
          headline-based summaries, it is well-suited for training deep neural networks. The dataset directly uses
          headlines as summaries. `English` `News` `Large`
        - [EUR-Lex-Sum](https://huggingface.co/datasets/dennlinger/eur-lex-sum): This is a high-quality multilingual
          dataset designed for legal text summarization, derived from official summaries of European Union legal acts.
          Summaries are about 10 times longer than news-based datasets, making it a robust benchmark for long-context
          modeling. All validation and test samples are fully aligned across languages at the paragraph level, making
          cross-lingual experiments, such as generating a summary in English from a French source feasible and
          meaningful. It also prioritizes depth and legal clarity, with detailed references written by professionals.
          `English` `French` `Legal` `Small`
        - [Big Patent](https://huggingface.co/datasets/NortheasternUniversity/big_patent): This dataset consists of 1.3
          million records of U.S. patent documents along with human written abstractive summaries. `English` `Legal`
          `Large` `Long Document`
        - [billsum](https://huggingface.co/datasets/FiscalNote/billsum): It's a dataset on summarization of US
          Congressional and California state bills. `English` `Legal` `Small`
        - [BookSum](https://huggingface.co/datasets/kmfoda/booksum): This is a dataset created to advance long-form
          narrative summarization. It focuses on source material from the literature domain, including novels, plays,
          and stories, and features highly abstractive, human-written summaries. These summaries are provided at three
          levels of granularity—paragraph, chapter, and book—each representing an increasing level of summarization
          difficulty. `English` `Literature` `Small` `Multilevel` `Long Document`
    - Models:
        - GPT3
        - GPT3.5
        - GPT4
        - LLaMa
        - Claude 2
    - Evaluation Metrics:
        - With Ground Truth:
            - Overlap based metrics:
                - ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
                - BLEU (Bilingual Evaluation Understudy)
                - METEOR (Metric for Evaluation of Translation with Explicit ORdering)
            - Similarity based Metrics:
                - BERTScore and BARTScore
                - BLEURT
        - Without Ground Truth:
            - Similarity based Metrics:
                - PPL
                - BERT-iBLEU
                - FactCC
                - SummaC
            - LLM based Metrics:
                - Writing Quality Metrics: Prompt-based LLM metrics can assess overall writing quality across dimensions
                  like `consistency`, `relevance`, `fluency`, and `coherence`, potentially replicating human evaluation
                  methods.
                - Faithfulness and Factuality Metrics: LLMs can evaluate if summaries accurately represent the source
                  text. They can detect factual inconsistencies in `zero-shot` settings and assign higher scores to
                  factually consistent summaries. Methods exist for zero-shot faithfulness evaluation by leveraging
                  probability changes using foundation models. LLMs have also been used to annotate summaries for
                  factual consistency against the source.
2. ["This could save us months of work" - Use Cases of AI and Automation Support in Investigative Journalism](https://dl.acm.org/doi/10.1145/3706599.3719856)

   This paper is mainly used for the `user story survey` design. It describes a user study involving `semi-structured`
   interviews with eight investigative journalists to elicit practical use cases for AI and automation. The prototype
   shown during the interviews focused on automating web-based data collection using LLMs and
   Programming-by-Demonstration (PbD). The interviews explored how automation and AI fit into journalists' `workflows`,
   the `challenges` they face, and their ideas for supportive tools. The paper summarizes the findings from these
   interviews by presenting a taxonomy of potential automation scenarios and tasks, grouped into two main categories:
   `Collecting` and `Reporting`.

   In reporting, participants used LLMs to `summarize` text from documents or transcribed
   interviews. LLMs were also used for rewriting reports, generating news headlines, and assisting with text editing
   like outlining interview questions. While some used LLMs for "brainstorming inspiring ideas," others avoided using
   them for rephrasing or copy editing to preserve originality. Automation in storytelling, including using AI
   illustrators and print layout systems, was also touched upon.

3. [Automatic Summarization of Long Documents](https://arxiv.org/abs/2410.05903)
    - Datasets:
        - [GovReport](https://gov-report-data.github.io/): The GovReport dataset consists of reports written by
          government research agencies, including the Congressional Research Service (CRS) and the U.S. Government
          Accountability Office (GAO).
          This dataset is notable for containing documents with a maximum word count exceeding 70,000. `English` `Legal`
          `Large` `Long Document`
        - BigPatent
    - Models:
        - GPT3.5
        - LLaMA-7B
    - How to summarize long documents:
        - Central Truncation: This is described as the most common and straightforward approach. It involves retaining
          only a portion of the document that fits within the context size by effectively discarding the middle section.
        - Document Skimming: Inspired by speed reading, this method involves selectively skipping parts of the text. The
          document is first segmented into smaller parts. Segments are then sampled uniformly with a probability `p`.
          The sampled segments are concatenated and sent to the model, ensuring the model sees a segment from each part
          of the text.
        - Summarization with Keyword Extraction: This approach attempts to use the entirety of the text by first
          extracting important keywords that capture the document's core meaning.
    - Evaluation Metrics:
      - ROUGE
      - BERTScore
