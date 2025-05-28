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
        - T5
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

4. [Argumentative Segmentation Enhancement for Legal Summarization](https://export.arxiv.org/pdf/2307.05081v1.pdf)
    - Datasets:
        - [The legal decision summarization dataset](https://www.canlii.org/?origLang=en): It is provided by the
          Canadian Legal Information Institute (CanLII).
          The summaries are prepared by attorneys, members of legal societies, or law students. The court decisions
          involve a wide variety of legal claims. The average length of the court decisions is 4,382 tokens. It exceeds
          the token limitation of GPT-3.5 (4,097 tokens).
    - Models:
        - GPT3.5
        - GPT4
        - LED
        - T5
        - BART
    - How to summarize long documents:
        - Argumentative Segmentation: The proposed method involves cutting the long documents into shorter segments
          while preserving argumentative components. A task of automatically classifying these segments as argumentative
          or non-argumentative is proposed, stemming from the idea of `Argumentative Zoning (AZ)`. This involves
          examining whether any argumentative sentences exist in a segment. The source utilizes a domain-independent
          linear text segmentation algorithm, `C99`, to split legal case decisions into segments.
    - Evaluation Metrics:
        - ROUGE
        - BLEU
        - METEOR
        - BERTScore

5. [Element-aware Summarization with Large Language Models: Expert-aligned Evaluation and Chain-of-Thought Method](https://aclanthology.org/2023.acl-long.482/)
    - Datasets:
        - [CNN/Daily Mail](https://paperswithcode.com/dataset/cnn-daily-mail-1): This is a dataset for news
          summarization. Abstractive summary bullets were written from news stories in CNN and Daily
          Mail websites as questions (with one of the entities hidden), and stories as the corresponding passages from
          which the system is expected to answer the fill-in the-blank question. The authors released the scripts that
          crawl, extract and generate pairs of passages and questions from these websites.
        - [XSum](https://paperswithcode.com/dataset/xsum): This is a dataset for evaluation of abstractive
          single-document summarization systems. The articles are collected from BBC articles (2010 to 2017) and cover a
          wide variety of domains (e.g., News, Politics, Sports, Weather, Business, Technology, Science, Health, Family,
          Education, Entertainment, and Arts).
    - Models:
        - GPT3
        - BART
        - T5
        - PEGASUS
    - How to summarize long documents:
        - Core element extraction: The LLM is prompted with the (truncated) source document and guiding
          questions to extract key elements (Entity, Date, Event, Result).
        - Multiple information integration and summarization: The LLM is then prompted with the truncated
          source document, the questions, and the extracted answers to generate the final summary.
    - Evaluation Metrics:
        - ROUGE
        - BERTScore
        - Precision, Recall, F1 score for subtasks
        - `Human evaluation` on `Fluency`, `Coherence`, `Consistency`, and `Relevance`

6. [Automatic Semantic Augmentation of Language Model Prompts (for Code Summarization)](https://dl.acm.org/doi/pdf/10.1145/3597503.3639183)

   This paper explores enhancing prompts for existing LLMs (code-davinci-002, text-davinci-003, `GPT-3.5-turbo`) by
   adding semantic facts for code summarization and completion. Evaluation relies primarily on `BLEU-4`, also reporting
   BLEU-DC, `ROUGE-L`, and `METEOR`, along with Exact Match/Edit Similarity for code completion, using statistical
   tests.
   They handle the limited prompt size (around 4K tokens) by automatically `reducing the number of few-shot exemplars`
   when the prompt becomes too long. The dataset used is `CodeSearchNet`, from which they sample 1000 examples per
   language for evaluation.

7. [Distilled GPT for Source Code Summarization](https://arxiv.org/pdf/2308.14731)

   This work describes distilling the code summarization ability of `GPT-3.5` into smaller local models (including jam
   and starcoder Transformer variants, and other encoder-decoder models). Evaluation metrics include automated scores
   like `METEOR`and `USE`, and human evaluation on `accuracy`, `completeness`, `concision`, and `overall preference`.
   Datasets include the funcom-java-long dataset with human summaries, and a larger corpus created by using
   GPT-3.5 to generate summaries for millions of Java methods, which serves as the primary training data for
   distillation.

8. [TriSum: Learning Summarization Ability from Large Language Models with Structured Rationale](https://aclanthology.org/2024.naacl-long.154.pdf)

   This paper focuses on distilling LLM capabilities into a smaller `BART-Large` model by training it on
   rationales and summaries generated by a larger model, `GPT-3.5`. Performance is evaluated using `ROUGE-F1` and
   `BERTScore`/`BARTScore`, comparing against numerous abstractive summarization baselines. Datasets used are
   `CNN/DailyMail`, `XSum`, and
   a custom `ClinicalTrial` dataset built from clinicaltrials.gov; they generate synthetic training data (rationales and
   summaries) from the documents and ground-truth summaries in these datasets using the LLM.

9. [Product Description and QA Assisted Self-Supervised Opinion Summarization](https://aclanthology.org/2024.findings-naacl.150.pdf)

   This source investigates multi-source opinion summarization, proposing their MEDOS framework which uses separate
   encoders for reviews, product descriptions, and question-answers, and compares it to various extractive, abstractive,
   concatenated multi-source, and LLM baselines. Evaluation relies on `ROUGE`, `F1 scores`, and `human assessments` of
   `faithfulness`, `coherence`, `conciseness`, and `fluency`. A limitation is that the model architecture is limited by
   input
   size, making it challenging to handle the large number of reviews sometimes available. For data, they use `Amazon`,
   `Oposum+`, and `Flipkart`, but lacking human summaries incorporating all sources, they extended test sets and used
   ChatGPT to generate new reference summaries, also creating synthetic training data from available corpora.

10. [An Iterative Optimizing Framework for Radiology Report Summarization With ChatGPT](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10433180)

    The paper proposes using their ImpressionGPT framework, which leverages the in-context
    learning of `ChatGPT` via a dynamic prompt and iterative optimization, for `radiology
    report` summarization. They evaluate performance using automated metrics including ROGUE,
    the Factual Consistency (FC) metric (`Precision`, `Recall`, and `F1 score`), and `BERTScore`. They
    utilize two public datasets, `MIMIC-CXR` and `OpenI`, filtering out ineligible reports based on criteria like minimum
    word counts in sections; these datasets provide the corpus from which similar reports are selected to construct
    dynamic prompts and guide the iterative optimization process, without requiring additional training data or
    fine-tuning the LLMs themselves.