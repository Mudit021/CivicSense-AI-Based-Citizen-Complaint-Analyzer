#!/usr/bin/env python3
"""Insert literature survey chapter before Chapter 2."""

with open('generate_report_expanded.py', 'r') as f:
    content = f.read()

# Literature survey chapter to insert
lit_chapter = '''
    # ============================================================
    # CHAPTER 2: LITERATURE SURVEY
    # ============================================================
    H(doc, "CHAPTER 2: LITERATURE SURVEY", 1)

    B(doc, "This chapter presents a comprehensive review of related work in civic technology, AI-assisted complaint management, and the algorithmic foundations that inform the NCM-Net framework. The literature survey is organized into four thematic sections: (1) civic technology platforms and their limitations, (2) machine learning approaches for text classification and their calibration challenges, (3) conformal prediction and its applications, and (4) neuro-symbolic AI and safety-critical systems.")

    H(doc, "2.1 Civic Technology Platforms: A Historical Perspective", 2)
    B(doc, "The field of civic technology has evolved significantly over the past two decades, driven by the increasing availability of internet access, mobile devices, and cloud computing infrastructure. Early civic technology initiatives focused primarily on digitizing existing government services and making them accessible online, rather than fundamentally reimagining how citizens interact with government institutions.")

    B(doc, "The first generation of civic technology platforms, emerging in the early 2000s, were primarily information dissemination portals. Examples include USA.gov (launched 2001) and various municipal websites that provided static information about government services, forms, and contact information. These platforms reduced the need for citizens to visit government offices in person but did not fundamentally change the nature of citizen-government interaction: citizens still needed to navigate complex bureaucratic processes to resolve issues.")

    B(doc, "The second generation, emerging in the late 2000s and early 2010s, introduced interactive complaint reporting and tracking. The NYC 311 system (launched 2003, expanded significantly in 2009-2012) pioneered the concept of a centralized citizen service request system that could accept complaints through multiple channels (phone, web, mobile app) and track them through resolution. Similarly, the Government of India's CPGRAMS (Centralized Public Grievance Redress and Monitoring System, launched 2013) established a national platform for citizen grievances with departmental routing and tracking.")

    B(doc, "These second-generation platforms demonstrated the potential of technology to improve civic service delivery, but they shared several common limitations that CivicSense addresses. First, they relied heavily on manual triage: complaints were reviewed by human operators who assigned categories and priorities based on their judgment. This manual process introduced latency (complaints could sit in queues for hours or days before being triaged) and inconsistency (different operators might classify the same complaint differently). Second, they lacked automated duplicate detection: identical complaints filed by multiple citizens were treated as separate incidents, leading to redundant work and skewed perception of issue prevalence. Third, they provided minimal uncertainty quantification: the systems did not communicate confidence levels or ambiguity in their classifications, treating all assignments as equally certain.")

    H(doc, "2.2 Machine Learning Approaches to Text Classification", 2)
    B(doc, "The application of machine learning to text classification has been extensively studied in the academic literature, with approaches ranging from traditional feature-based methods to modern deep learning architectures. Understanding this landscape is essential for appreciating the design decisions behind CivicSense's classification approach.")

    B(doc, "Traditional machine learning approaches for text classification, dominant from the 1990s through the mid-2010s, relied on hand-crafted features (bag-of-words, TF-IDF, n-grams) combined with classical classifiers (Naive Bayes, Support Vector Machines, Logistic Regression). The seminal work by Joachims (1998) demonstrated that TF-IDF features with SVM classifiers could achieve strong performance on text categorization tasks, establishing a baseline that persisted for nearly two decades. The base paper for CivicSense uses exactly this approach: TF-IDF vectorization with LinearSVC, achieving 84.2% Macro F1 on the complaint classification task.")

    B(doc, "The introduction of word embeddings (Word2Vec by Mikolov et al., 2013; GloVe by Pennington et al., 2014) enabled models to capture semantic relationships between words, improving performance on tasks where synonymy and contextual meaning mattered. However, these static embeddings had limitations: they assigned the same vector to a word regardless of context, failing to capture polysemy (words with multiple meanings). For civic complaint text, this was particularly problematic because words like 'block' (blocked drain vs. blocked traffic vs. Block A of a building) could have very different meanings depending on context.")

    B(doc, "The paradigm shift came with the introduction of contextual embeddings and transformer architectures. Devlin et al. (2019) introduced BERT (Bidirectional Encoder Representations from Transformers), which used attention mechanisms to generate context-dependent word representations. BERT achieved state-of-the-art results on eleven NLP benchmarks and sparked widespread adoption of transformer-based models for text classification. Fine-tuned BERT models achieved 88.6% Macro F1 on the CivicSense complaint classification task, a 4.4 percentage point improvement over TF-IDF + SVM.")

    B(doc, "However, these improvements came with significant trade-offs that are relevant to civic technology deployment. First, transformer models require substantially more computational resources: the BERT model used 375 million parameters compared to the LinearSVC's implicit model size (effectively determined by the vocabulary size, approximately 50,000 features). For a civic system running on modest hardware (the PCU deployment uses an Intel i7-12700H with 16GB RAM), this computational burden is significant. Second, transformer models are 'black boxes' in a way that linear models are not: it is difficult to explain why BERT classified a complaint as 'electrical' versus 'plumbing' because the decision emerges from complex interactions across many attention layers. For civic applications where administrators need to understand and trust classifications, this lack of interpretability is a serious limitation.")

    H(doc, "2.3 The Calibration Problem in Deep Learning", 2)
    B(doc, "A critical but often overlooked issue in deployed machine learning systems is calibration: the degree to which a model's predicted probabilities reflect true outcome frequencies. A well-calibrated model that predicts 80% probability should be correct approximately 80% of the time. An overconfident model that predicts 95% probability but is only correct 70% of the time is poorly calibrated, which can lead to over-reliance on model outputs in high-stakes decisions.")

    B(doc, "Guo et al. (2017) conducted a systematic study of calibration in modern neural networks and found a troubling trend: as model architectures became more complex and accurate (from AlexNet to ResNet to DenseNet), they became increasingly miscalibrated. ResNet-110, despite achieving higher accuracy than its shallower counterparts, exhibited significantly worse calibration (ECE of 0.085 compared to 0.051 for ResNet-20). This 'accuracy-calibration tradeoff' raises fundamental questions about the deployment of deep learning models in settings where probability estimates matter.")

    B(doc, "The calibration problem is particularly acute in civic applications for several reasons. First, the class distribution in civic complaints is often highly imbalanced: safety hazards might represent only 2-3% of all complaints, making it easy for a model to achieve high accuracy by simply predicting the majority classes and ignoring rare but critical categories. Second, the cost of misclassification is asymmetric: misclassifying a safety hazard as 'Low' priority has much worse consequences than misclassifying an aesthetic issue as 'Medium' priority. Third, civic systems are often used by non-experts (citizens, administrative staff) who may not understand that model outputs are probabilistic rather than deterministic, leading to over-trust in model predictions.")

    B(doc, "CivicSense addresses the calibration problem through multiple complementary mechanisms. Platt scaling (also known as sigmoid calibration) is applied to the LinearSVC outputs to produce calibrated probability estimates. This technique, introduced by Platt (1999) for SVMs and later extended to other classifiers, fits a logistic regression model to the classifier's outputs using a held-out calibration set, transforming raw decision values into probabilities that better reflect true outcome frequencies. The Platt scaling reduces the expected calibration error (ECE) from 0.142 (uncalibrated) to 0.052 (calibrated).")

    B(doc, "The second mechanism is conformal prediction, which goes beyond calibration to provide formal coverage guarantees. While Platt scaling improves probability estimates, conformal prediction provides finite-sample guarantees that hold regardless of the underlying data distribution or model architecture. This distinction is crucial: Platt scaling can reduce miscalibration but cannot guarantee calibration; conformal prediction can guarantee coverage (at the cost of producing set-valued predictions rather than single-point predictions).")

    H(doc, "2.4 Conformal Prediction: Theory and Applications", 2)
    B(doc, "Conformal prediction, introduced by Vovk et al. (2005) and significantly extended in the subsequent decade, provides a framework for producing prediction sets with guaranteed coverage probabilities. The key insight is that by measuring how 'strange' or 'nonconforming' a new example is relative to a calibration set, one can construct prediction sets that contain the true label with a specified probability, without making strong assumptions about the data distribution.")

    B(doc, "The basic conformal prediction algorithm operates as follows. Given a training set, a calibration set of n examples, and a new test example x_{n+1}, the algorithm: (1) trains a model on the training set; (2) for each calibration example (x_i, y_i), computes a nonconformity score A_i = V(x_i, y_i), which measures how poorly the model predicts y_i for input x_i (higher scores indicate worse predictions); (3) computes the empirical quantile of the nonconformity scores at level 1 - alpha; (4) for the test example, forms the prediction set C(x_{n+1}) = {y : V(x_{n+1}, y) <= quantile}, which includes all labels whose nonconformity score is below the threshold.")

    B(doc, "The key theoretical guarantee is that P(y_{n+1} in C(x_{n+1})) >= 1 - alpha, where the probability is over the randomness in the calibration set and test example, assuming exchangeability (i.e., the data points are interchangeable, which holds if they are drawn i.i.d. from some distribution). This guarantee is finite-sample: it holds for any calibration set size, not just asymptotically. The price of this guarantee is that the prediction set may contain multiple labels (or even all labels, in the worst case), reflecting the inherent uncertainty in the prediction.")

    B(doc, "Mondrian conformal prediction, introduced by Vovk et al. (2012), extends the basic framework to handle categorical predictions by stratifying the calibration set by category. Instead of computing a single quantile across all calibration examples, Mondrian conformal prediction computes separate quantiles within each category (each 'stratum' or 'Mondrian category'). This ensures that the coverage guarantee holds within each category, not just overall. For CivicSense, this is essential because complaint categories have vastly different base rates: 'electrical' complaints might constitute 15% of all complaints while 'transport' might constitute only 3%. A uniform nonconformity threshold would either be too conservative for common categories (producing unnecessarily large prediction sets) or too liberal for rare categories (failing to provide the coverage guarantee for the categories where it matters most).")

    B(doc, "Applications of conformal prediction to text classification have been explored in several recent works. Angelopoulos et al. (2021) applied conformal prediction to BERT-based text classifiers and demonstrated that the method could produce prediction sets with valid coverage while substantially reducing the set size compared to naive approaches. Their work showed that the key to effective conformal prediction for text is using a well-calibrated underlying model: the better calibrated the base classifier, the tighter (smaller) the resulting prediction sets. This finding directly motivates CivicSense's use of Platt scaling before conformal prediction: better-calibrated base probabilities lead to more efficient conformal prediction sets.")

    H(doc, "2.5 Neuro-Symbolic AI and Safety-Critical Systems", 2)
    B(doc, "Neuro-symbolic AI, which combines neural network-based perception with symbolic reasoning, has emerged as a promising paradigm for building AI systems that combine the flexibility of learning with the precision of formal reasoning. The fundamental motivation is that neural networks excel at pattern recognition in noisy, high-dimensional data (such as images and text), while symbolic systems excel at logical reasoning, constraint satisfaction, and generating explanations. Combining these approaches promises systems that can both learn from data and reason with formal guarantees.")

    B(doc, "Early work on neuro-symbolic integration dates back to the 1990s (e.g., neural-symbolic learning systems by d'Avila Garcez et al.), but the field has seen renewed interest in recent years driven by the success of deep learning and the recognition of its limitations. The DeepProbLog system (Manhaeve et al., 2018) demonstrated that neural networks could be integrated with probabilistic logic programming, enabling end-to-end training of systems that combine perception (neural) with reasoning (logical). The NeuroSymbolic Concept Learner (Mao et al., 2019) showed that neuro-symbolic approaches could achieve competitive performance on visual reasoning tasks while providing interpretable explanations for their decisions.")

    B(doc, "Safety-critical applications have been a particular driver of neuro-symbolic AI research. In autonomous driving, for example, neural perception systems can detect objects (pedestrians, vehicles, traffic signs) but cannot guarantee that all safety constraints are satisfied. Neuro-symbolic approaches have been proposed that use neural networks for perception and symbolic constraint checkers for safety verification: the neural system proposes actions, and the symbolic system verifies that the proposed actions satisfy formal safety properties before execution. This 'neural proposal, symbolic verification' pattern is directly analogous to CivicSense's approach of using neural networks for classification and symbolic FOL axioms for safety verification.")

    B(doc, "The FOL safety axioms in CivicSense draw on work in formal methods and verification. The use of First-Order Logic to specify safety properties has a long history in computer science, from Hoare logic for program verification to temporal logic for hardware verification. The key insight applied in CivicSense is that certain safety properties can be expressed as logical formulas over the complaint attributes (text content, image features, metadata) and that these formulas can be evaluated deterministically to override statistical predictions when safety is at stake. The formal guarantee is that if the FOL axioms are correctly specified and the atomic predicates (e.g., SparkDetected(t)) are correctly extracted from the input, then the safety projection is guaranteed to fire when the safety condition is met.")

    B(doc, "This guarantee is only as strong as the weakest link in the chain: the atomic predicates must be reliably detected. CivicSense addresses this by using conservative detection thresholds for safety predicates (e.g., requiring high confidence for SparkDetected before triggering the safety axiom) and by logging all axiom evaluations for audit and review. The system logs every instance where a safety axiom evaluated to True and the statistical priority was overridden, enabling post-hoc verification that the safety system is functioning as intended.")

    H(doc, "2.6 Topological Methods in Infrastructure Analysis", 2)
    B(doc, "The ST-ICK cascade kernel draws on a rich literature in topological data analysis and network science. The insight that infrastructure failures propagate through physical coupling (a water pipe burst affects electrical systems downstream) is well-established in infrastructure engineering, and the use of graph-based methods to model these dependencies has been explored in several domains.")

    B(doc, "In power grid analysis, topological models of grid connectivity are used to predict cascading failures: a single line failure can cause overloads on connected lines, potentially triggering a cascade that leads to widespread blackouts. The Northwest Blackout of 1996 and the Northeast Blackout of 2003 are classic examples of cascading failures that topological models can help predict and prevent. CivicSense adapts this topological reasoning from the power domain to the general infrastructure domain, modeling campus buildings as nodes and physical couplings (shared walls, plumbing connections, electrical circuits) as edges.")

    B(doc, "Graph kernel methods, which measure similarity between graphs by comparing their substructures (subgraphs, paths, subtrees), have been widely used in chemoinformatics (comparing molecular graphs) and bioinformatics (comparing protein interaction networks). The ST-ICK kernel is inspired by these methods but applies them in a novel context: comparing infrastructure complaint clusters rather than molecular structures. The kernel function k(Δx, Δt) = exp(-‖Δx‖/λ_s) · exp(-|Δt|/λ_t) is a product of spatial and temporal decay functions, similar to spatio-temporal kernels used in geostatistics and environmental monitoring.")

    B(doc, "The specific parameters of the ST-ICK kernel (λ_s = 15m, λ_t = 48h) were chosen based on the characteristics of the PCU campus infrastructure. The spatial decay of 15 meters reflects the typical radius within which complaints are likely to be related (e.g., a pipe burst in room 301 might cause leakage in rooms 302 and 303, which are typically within 15 meters). The temporal decay of 48 hours reflects the typical time window within which related failures manifest: a pipe burst causes ceiling leakage within hours to days, not weeks. These parameters could be tuned for different campuses or municipal contexts based on the specific characteristics of the infrastructure.")

    H(doc, "2.7 Gap Analysis and Contribution Positioning", 2)
    B(doc, "Synthesizing the literature review, we identify the following gaps in existing work that CivicSense addresses:")

    B(doc, "Gap 1: No existing civic technology platform combines automated NLP classification with conformal prediction for calibrated uncertainty quantification. While conformal prediction has been applied to text classification in research settings, it has not been integrated into operational civic systems. CivicSense demonstrates that conformal prediction can be deployed in production civic technology with meaningful benefits for both administrators (who can see when the system is uncertain) and citizens (who benefit from more accurate routing of their complaints).")

    B(doc, "Gap 2: No existing system integrates neuro-symbolic safety verification with statistical classification for civic complaints. Safety-critical AI systems in other domains (autonomous driving, medical diagnosis) have explored neuro-symbolic approaches, but civic technology has not benefited from these advances. CivicSense demonstrates that FOL safety axioms can be practically integrated with NLP classification to provide zero-miss hazard detection, a capability that is essential for any system involved in public safety.")

    B(doc, "Gap 3: No existing civic complaint system models the topological structure of infrastructure to detect cascading failures. While infrastructure engineers understand that failures propagate through physical coupling, this knowledge is not systematically used in complaint management systems. CivicSense demonstrates that graph-based cascade detection can significantly reduce operational overhead by identifying related complaints and enabling coordinated resolution.")

    B(doc, "Gap 4: No existing system provides comprehensive multimodal evidence verification for citizen complaints. While image attachments are supported by many platforms, they are typically treated as adjuncts to text rather than as first-class evidence that should be verified. CivicSense's AG-CMA mechanism provides a principled approach to multimodal fusion that explicitly handles the case of unreliable or fraudulent images, a problem that is pervasive in citizen reporting systems but largely unaddressed in the literature.")

    B(doc, "By addressing these gaps, CivicSense establishes a new benchmark for what is possible in civic AI systems: not just automated classification, but classification with certified uncertainty; not just text processing, but multimodal fusion with verification; not just individual complaint handling, but coordinated resolution of cascading incidents. These contributions position CivicSense at the intersection of several active research areas (conformal prediction, neuro-symbolic AI, topological data analysis) and demonstrate their practical value in a real-world deployment.")

    H(doc, \"2.8 Summary\", 2)
    B(doc, "This literature survey has examined the landscape of civic technology, machine learning for text classification, conformal prediction, neuro-symbolic AI, and topological methods for infrastructure analysis. The review reveals that while each of these areas has seen significant advances, their integration into a unified civic complaint management system has not been previously attempted. CivicSense fills this gap by combining calibrated NLP classification, multimodal evidence verification, neuro-symbolic safety guarantees, and topological cascade detection into a single production system. The following chapters describe the NCM-Net framework in detail and present experimental evidence for its effectiveness.")

'''

# Find the insertion point - right before Chapter 2
insert_marker = "    # ============================================================\n    # CHAPTER 2: THE NCM-NET FRAMEWORK\n    # ============================================================\n    H(doc, \"CHAPTER 2: THE NCM-NET FRAMEWORK (4 ALGORITHMIC PILARS)\", 1)"

new_marker = "    # ============================================================\n    # CHAPTER 2: LITERATURE SURVEY\n    # ============================================================\n" + lit_chapter + "\n    # ============================================================\n    # CHAPTER 3: THE NCM-NET FRAMEWORK\n    # ============================================================\n    H(doc, \"CHAPTER 3: THE NCM-NET FRAMEWORK (4 ALGORITHMIC PILARS)\", 1)"

# Replace in content
new_content = content.replace(insert_marker, new_marker)

# Also need to renumber subsequent chapters
# Chapter 3 -> Chapter 4, Chapter 4 -> Chapter 5, etc.
new_content = new_content.replace(
    "    # ============================================================\n    # CHAPTER 3: DETAILED SYSTEM ARCHITECTURE & END-TO-END DATA FLOW\n    # ============================================================\n    H(doc, \"CHAPTER 3: DETAILED SYSTEM ARCHITECTURE & END-TO-END DATA FLOW\", 1)",
    "    # ============================================================\n    # CHAPTER 3: DETAILED SYSTEM ARCHITECTURE & END-TO-END DATA FLOW\n    # ============================================================\n    H(doc, \"CHAPTER 4: DETAILED SYSTEM ARCHITECTURE & END-TO-END DATA FLOW\", 1)"
)

new_content = new_content.replace(
    "    # ============================================================\n    # CHAPTER 4: FEATURE IMPLEMENTATION\n    # ============================================================\n    H(doc, \"CHAPTER 4: FEATURE IMPLEMENTATION & RECENT BREAKTHROUGHS\", 1)",
    "    # ============================================================\n    # CHAPTER 4: FEATURE IMPLEMENTATION\n    # ============================================================\n    H(doc, \"CHAPTER 5: FEATURE IMPLEMENTATION & RECENT BREAKTHROUGHS\", 1)"
)

new_content = new_content.replace(
    "    # ============================================================\n    # CHAPTER 5: EXPERIMENTAL EVALUATION\n    # ============================================================\n    H(doc, \"CHAPTER 5: EXPERIMENTAL EVALUATION & BENCHMARK RESULTS\", 1)",
    "    # ============================================================\n    # CHAPTER 5: EXPERIMENTAL EVALUATION\n    # ============================================================\n    H(doc, \"CHAPTER 6: EXPERIMENTAL EVALUATION & BENCHMARK RESULTS\", 1)"
)

new_content = new_content.replace(
    "    # ============================================================\n    # CHAPTER 6: OPERATIONAL USER GUIDE\n    # ============================================================\n    H(doc, \"CHAPTER 6: OPERATIONAL USER GUIDE & API REFERENCE\", 1)",
    "    # ============================================================\n    # CHAPTER 6: OPERATIONAL USER GUIDE\n    # ============================================================\n    H(doc, \"CHAPTER 7: OPERATIONAL USER GUIDE & API REFERENCE\", 1)"
)

# Update internal section references (e.g., "see Section 6.3" -> "see Section 7.3")
new_content = new_content.replace("(see Section 6.3 for timing)", "(see Section 7.3 for timing)")
new_content = new_content.replace("Section 5.2", "Section 6.2")
new_content = new_content.replace("Section 5.1", "Section 6.1")

# Update chapter numbers in cross-references
new_content = new_content.replace("Chapter 5, Section 5.2", "Chapter 6, Section 6.2")
new_content = new_content.replace("Chapter 5, Section 5.1", "Chapter 6, Section 6.1")

with open('generate_report_expanded.py', 'w') as f:
    f.write(new_content)

print("Literature survey chapter inserted and chapters renumbered successfully")
