#!/usr/bin/env python3
"""Append additional content to the report generator."""

with open('generate_report_expanded.py', 'r') as f:
    content = f.read()

# Additional content to insert before the APPENDIX A section
extra_content = '''

    # ============================================================
    # CHAPTER 7: CONCLUSION
    # ============================================================
    H(doc, "CHAPTER 7: CONCLUSION & FUTURE SCOPE", 1)

    H(doc, "7.1 Summary of Contributions", 2)
    B(doc, "CivicSense represents a significant advancement in the field of civic AI systems, contributing to both academic research and practical civic administration in the following ways:")

    B(doc, "First Contribution: Mathematical Rigor in Civic AI. Unlike most civic technology projects that rely on heuristic approaches or uncalibrated machine learning models, CivicSense introduces formal mathematical guarantees through three complementary mechanisms: Mondrian Conformal Prediction for calibrated uncertainty quantification with finite-sample coverage guarantees, First-Order Logic safety axioms for deterministic zero-miss hazard detection, and Asymmetric Gated Cross-Modal Alignment for verifiable evidence validation. These mathematical foundations establish CivicSense as the first civic AI system with provable reliability properties rather than empirical performance alone.")

    B(doc, "Second Contribution: Multimodal Fusion with Verification. The AG-CMA mechanism introduces a novel approach to multimodal fusion that explicitly addresses the problem of unreliable visual inputs. Rather than naively combining text and image features, the asymmetric gating mechanism dynamically adjusts the influence of visual modalities based on evidence quality, providing a principled solution to the pervasive problem of spam images and visual hallucinations in citizen reporting systems.")

    B(doc, "Third Contribution: Operational Efficiency through Cascade Detection. The ST-ICK kernel demonstrates that topological reasoning about infrastructure coupling can dramatically reduce operational overhead in complaint resolution. The 63% reduction in duplicate dispatches translates directly to cost savings and faster resolution times, demonstrating that graph-based reasoning about physical infrastructure can yield practical benefits beyond what pure NLP approaches achieve.")

    B(doc, "Fourth Contribution: Production-Grade Deployment. Unlike many academic prototypes that are evaluated only on static benchmarks, CivicSense has been deployed as a live production system serving real users at Pimpri Chinchwad University. The system has processed hundreds of genuine complaints across 15+ buildings, providing real-world validation of the proposed approaches under authentic operational conditions including network variability, user behavior patterns, and integration with existing administrative workflows.")

    H(doc, "7.2 Comparative Analysis with Related Work", 2)
    B(doc, "The following table positions CivicSense against related work in civic technology, AI-assisted complaint management, and conformal prediction applications:")

    TH(doc,
        ["System / Approach", "Year", "Key Features", "Limitations Addressed by CivicSense"],
        [
            ("CPGRAMS (Govt of India)", "2013", "National Grievance Portal, manual routing, email-based tracking", "No automated classification; manual triage latency of days/weeks; no evidence validation; no duplicate detection"),
            ("Singapore OneService", "2016", "Mobile-first citizen reporting, location-based routing, issue categorization", "Rule-based categorization (no ML); no confidence calibration; no safety guarantees; no multimodal evidence verification"),
            ("NYC 311 System", "2003", "Voice/online complaint intake, agent-assisted routing, status tracking", "High manual operational cost; limited automation; no uncertainty quantification; no cascade detection"),
            ("BERT-based Text Classification (Devlin et al.)", "2019", "State-of-the-art NLP classification, transfer learning from large corpora", "Uncalibrated outputs; no conformal guarantees; no vision integration; no safety constraints; no cascade awareness"),
            ("Conformal Prediction for NLP (Angelopoulos et al.)", "2021", "Distribution-free uncertainty quantification for text classifiers", "Applied to single modality only; no deployment in civic context; no integration with safety constraints or multimodal verification"),
            ("CivicSense NCM-Net (This Work)", "2025", "Multimodal AI with certified uncertainty, neuro-symbolic safety guarantees, cascade detection, 1-click batch resolution", "N/A - addresses all identified limitations from prior systems"),
        ],
        col_widths=[1.4, 0.5, 2.0, 2.5], fs=8
    )

    H(doc, "7.3 Limitations and Caveats", 2)
    B(doc, "While CivicSense demonstrates significant advances over existing systems, several limitations should be acknowledged for honest assessment:")

    BL(doc, [
        "Domain Specificity: The current deployment is specific to Pimpri Chinchwad University campus infrastructure complaints. Generalization to other domains (municipal governance, healthcare complaints, transportation issues) would require domain-specific adaptation of the category taxonomy, safety axioms, and cascade graph structure. Transfer learning across domains is an active area of future research.",
        "Language Limitation: The NLP classifier is trained primarily on English-language complaints. Marathi and Hindi language complaints, which represent a significant portion of citizen communications in the region, are currently handled through manual translation or Google Translate preprocessing, which may introduce classification errors. The planned Whisper integration for voice note translation addresses this partially.",
        "Scalability Considerations: The current single-server deployment with SQLite is suitable for campus-scale deployment (hundreds to low thousands of complaints). Municipal-scale deployments (millions of complaints) would require migration to PostgreSQL with partitioning, introduction of message queue systems for asynchronous processing, and horizontal scaling of the classification service.",
        "Adversarial Robustness: While the fraud detection system catches common spam patterns, sophisticated adversaries could potentially craft complaints that evade detection (e.g., generating text with appropriate keywords but false information, or using AI-generated images that pass dHash and visual quality checks). Adversarial robustness testing and detection of AI-generated content are important future security considerations.",
        "Cold Start Problem: The conformal prediction calibration requires a sufficient calibration set (currently 250+ complaints) to provide reliable coverage guarantees. For entirely new complaint categories or deployment in new domains, the calibration guarantee may not hold until sufficient data is collected. Methods for cold-start conformal prediction are under investigation.",
    ], after=Pt(4))

    H(doc, "7.4 Future Research Directions", 2)
    B(doc, "The following research directions represent promising avenues for extending CivicSense:")

    B(doc, "Federated Multi-Campus Learning: Rather than centralizing complaint data from multiple universities (which raises privacy concerns and data governance complexities), federated learning would enable collaborative model improvement across institutions while keeping complaint data localized. Each campus would train local model updates on their data, and only encrypted model parameter updates would be aggregated centrally. This approach preserves data sovereignty while enabling the benefits of larger training corpora.")

    B(doc, "Multilingual Voice-First Interface: Expanding beyond text-based complaints to support voice notes in Marathi, Hindi, and English would dramatically improve accessibility for citizens who are more comfortable speaking than typing. OpenAI Whisper provides high-quality speech-to-text transcription, but domain-specific fine-tuning on civic complaint vocabulary would improve accuracy for technical terms (e.g., specific building names, infrastructure component terminology).")

    B(doc, "IoT-Integrated Predictive Detection: Rather than relying on citizen complaints to detect infrastructure problems, integration with IoT sensors (water pressure sensors, electrical current monitors, structural vibration sensors) could enable predictive detection of infrastructure failures before they generate complaints. This would shift the system from reactive complaint handling to proactive infrastructure monitoring, potentially preventing issues from occurring in the first place.")

    B(doc, "Explainable AI for Administrative Transparency: While the current system surfaces confidence scores and prediction sets, deeper explainability could help administrators understand why specific classifications were made. Techniques such as LIME (Local Interpretable Model-agnostic Explanations) or SHAP (SHapley Additive exPlanations) could highlight which words or image features contributed most to the classification decision, building trust in the automated system and enabling administrators to catch potential misclassifications.")

    B(doc, "Blockchain-Anchored Audit Trail: For accreditation and legal compliance purposes, anchoring complaint records and resolution actions to a blockchain (e.g., Hyperledger Fabric for permissioned enterprise blockchain) would provide immutable proof of the complaint lifecycle. This would prevent tampering with historical records and enable cryptographic verification of resolution claims during external audits.")

    B(doc, "Active Learning for Continuous Improvement: Currently, the classification model is static after initial training. Implementing an active learning loop where uncertain predictions (|C(X)| > 1) are routed to human reviewers and their labels fed back into periodic model retraining would enable the system to continuously improve its accuracy over time, adapting to changing complaint patterns and emerging infrastructure issues.")

    H(doc, "7.5 Final Remarks", 2)
    B(doc, "CivicSense demonstrates that rigorous AI research can be successfully translated into production systems that deliver measurable real-world impact. The integration of conformal prediction, neuro-symbolic reasoning, and multimodal fusion addresses fundamental limitations of conventional civic technology while maintaining usability and operational efficiency.")

    B(doc, "The system is currently live at Pimpri Chinchwad University and is available for demonstration and evaluation by other academic institutions, municipal governments, and civic technology organizations. We welcome collaborations to adapt and extend CivicSense for broader deployment across diverse civic contexts.")

    B(doc, "The open-source release of the NCM-Net framework (planned for Q2 2026) will enable other researchers and civic technology practitioners to build upon these contributions, accelerating the development of reliable, verifiable AI systems for public service.")

    # ============================================================
    # APPENDIX A
    # ============================================================
    H(doc, "APPENDIX A: NCM-NET MATHEMATICAL FORMULATION SUMMARY", 1)
'''

# Insert before the APPENDIX A section
insert_point = content.find('    # ============================================================\n    # APPENDIX A')
if insert_point != -1:
    content = content[:insert_point] + extra_content + '\n' + content[insert_point:]
    with open('generate_report_expanded.py', 'w') as f:
        f.write(content)
    print('Content appended successfully')
else:
    print('Could not find insertion point - searching for APPENDIX A...')
    # Alternative: find and print context
    idx = content.find('APPENDIX A')
    if idx != -1:
        print(f'Found APPENDIX A at index {idx}')
        print(content[idx-50:idx+50])
