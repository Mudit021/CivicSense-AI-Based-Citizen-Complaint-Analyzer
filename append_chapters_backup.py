from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document("Project_Report_Master_backup.docx")

PRIMARY = RGBColor(26, 43, 76)
SECONDARY = RGBColor(59, 91, 219)
DARK = RGBColor(30, 41, 59)

def cell_bg(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    tcPr.append(shd)

def cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        '<w:tcMar %s'
        '><w:top w:w="%d" w:type="dxa"/>'
        '<w:bottom w:w="%d" w:type="dxa"/>'
        '<w:left w:w="%d" w:type="dxa"/>'
        '<w:right w:w="%d" w:type="dxa"/></w:tcMar>' % (nsdecls("w"), top, bottom, left, right)
    )
    tcPr.append(tcMar)

def heading(text, level=1, color=None, space_before=14):
    if color is None:
        color = PRIMARY
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before if level == 1 else 10)
    p.paragraph_format.space_after = Pt(8)
    sizes = {1: 16, 2: 13, 3: 11.5, 4: 10.5}
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(sizes.get(level, 10))
    r.font.bold = True if level <= 2 else (level == 3)
    r.font.color.rgb = color
    return p

def body(text, indent=False, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if indent:
        p.paragraph_format.left_indent = Inches(0.3)
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(10.5)
    r.font.color.rgb = DARK
    return p

def bullet(text, level=0, space_after=3):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.1
    p.paragraph_format.left_indent = Inches(0.4 + level * 0.25)
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(10)
    r.font.color.rgb = DARK
    return p

def callout(text, title='KEY INSIGHT:', bg='F0F7FF', border='1A2B4C'):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    cell_bg(cell, bg)
    cell_margins(cell, 80, 80, 120, 120)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        '<w:tcBorders %s'
        '><w:left w:val="single" w:sz="24" w:space="0" w:color="%s"/>'
        '<w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>' % (nsdecls("w"), border)
    )
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    rt = p.add_run(title)
    rt.font.name = 'Arial'
    rt.font.size = Pt(10)
    rt.font.bold = True
    rt.font.color.rgb = SECONDARY
    r = p.add_run(' ' + text)
    r.font.name = 'Arial'
    r.font.size = Pt(10)
    r.font.color.rgb = DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def table(headers, rows, col_widths=None, font_size=9):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    if col_widths:
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = Inches(w)
    for col_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, col_idx)
        cell_bg(cell, '1A2B4C')
        cell_margins(cell, 60, 60, 90, 90)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = 'Arial'
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
    for row_idx, row_data in enumerate(rows, start=1):
        bg_color = 'FFFFFF' if row_idx % 2 == 0 else 'F8FAFC'
        for col_idx, text in enumerate(row_data):
            cell = tbl.cell(row_idx, col_idx)
            cell_bg(cell, bg_color)
            cell_margins(cell, 50, 50, 80, 80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(text))
            r.font.name = 'Arial'
            r.font.size = Pt(font_size)
            r.font.color.rgb = DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    return tbl

def two_col(rows_data, left_width=2.2, right_width=4.3):
    tbl = doc.add_table(rows=len(rows_data), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(left_width)
    tbl.columns[1].width = Inches(right_width)
    for row_idx, (label, value) in enumerate(rows_data):
        cl = tbl.cell(row_idx, 0)
        cv = tbl.cell(row_idx, 1)
        cell_bg(cl, 'F1F5F9')
        cell_bg(cv, 'FFFFFF')
        cell_margins(cl, 50, 50, 90, 90)
        cell_margins(cv, 50, 50, 90, 90)
        pl = cl.paragraphs[0]
        pl.paragraph_format.space_before = Pt(0)
        pl.paragraph_format.space_after = Pt(0)
        rl = pl.add_run(label)
        rl.font.name = 'Arial'
        rl.font.size = Pt(9.5)
        rl.font.bold = True
        rl.font.color.rgb = DARK
        pv = cv.paragraphs[0]
        pv.paragraph_format.space_before = Pt(0)
        pv.paragraph_format.space_after = Pt(0)
        rv = pv.add_run(value)
        rv.font.name = 'Arial'
        rv.font.size = Pt(9.5)
        rv.font.color.rgb = DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

target_text = 'APPENDIX A: HOW TO RUN THE PROJECT'
target_para = None
for p in doc.paragraphs:
    if target_text in p.text:
        target_para = p
        break

if not target_para:
    print('ERROR: APPENDIX A not found')
    import sys
    sys.exit(1)

print('Anchor found')
parent = target_para._p.getparent()
idx = list(parent).index(target_para._p)
print('Anchor index: %d' % idx)

# CH23
print('Inserting Chapter 23')
p = doc.add_paragraph()
p.paragraph_format.page_break_before = True
r = p.add_run('CHAPTER 23: ADVANCED CLASSIFICATION TECHNIQUES AND MODEL OPTIMIZATION')
r.font.name = 'Arial'
r.font.size = Pt(16)
r.font.bold = True
r.font.color.rgb = PRIMARY
parent.insert(idx, p._p)
idx += 1

body('This chapter provides a comprehensive examination of advanced classification techniques applicable to civic complaint analysis. While CivicSense uses TF-IDF with LinearSVC for reliability and interpretability, understanding the broader landscape is essential for assessing options and planning improvements.')
heading('23.1 Classical Machine Learning Approaches', 2, space_before=12)
body('Classical methods remain highly relevant for text classification, especially with limited data and where interpretability matters. They have decades of study behind them and provide strong baselines that are difficult to outperform on small, well-structured tasks.')
heading('23.1.1 Naive Bayes Classifiers', 3, space_before=10)
body('Naive Bayes is a probabilistic classifier based on Bayes theorem assuming feature independence. Despite this simplifying assumption, it often performs well and serves as a strong baseline. Multinomial Naive Bayes is suited for document classification with word counts as features.')
table(
    ['Characteristic', 'Naive Bayes', 'Relevance to Civic Complaints'],
    [
        ['Training speed', 'Very fast (linear in documents x vocab)', 'Acceptable for periodic retraining'],
        ['Prediction speed', 'Very fast', 'Real-time triage feasible'],
        ['Data requirement', 'Tens to hundreds per class work', 'Matches current corpus size'],
        ['Probabilistic outputs', 'Natural (class posterior)', 'Confidence scores available'],
        ['Vocabulary handling', 'Requires fixed vocabulary', 'Needs periodic refresh'],
        ['Strengths', 'Simple, fast, interpretable', 'Good baseline and fallback'],
    ], [1.5, 2.2, 2.3], 9)
heading('23.1.2 Support Vector Machines', 3, space_before=10)
body('SVMs find the optimal hyperplane separating classes with maximum margin. LinearSVC is particularly effective for high-dimensional text data. The decision boundary is determined only by support vectors - the training examples closest to the boundary.')
table(
    ['Parameter', 'Effect', 'Typical Values for Text'],
    [
        ['C (regularization)', 'Higher C = narrower margin, fewer errors', '0.1 to 1.0 typical'],
        ['class_weight (balanced)', 'Adjusts loss for imbalanced classes', 'Helpful for fewer-shot categories'],
        ['dual', 'Which formulation to solve', 'dual=False for n_samples > n_features'],
        ['tol (tolerance)', 'Stopping criterion precision', '1e-4 typical'],
        ['max_iter', 'Iteration limit', 'Set high (5000+) for convergence'],
    ], [1.4, 2.2, 2.4], 9)
heading('23.1.3 Logistic Regression', 3, space_before=10)
body('Logistic regression estimates class probabilities using a sigmoid function (binary) generalized to softmax (multi-class). It is a convex optimization with a globally optimal solution, making it reliable and well-understood. It provides well-calibrated probability estimates.')
heading('23.2 Tree-Based Ensemble Methods', 2, space_before=12)
body('Tree-based ensemble methods offer a different approach: building decision trees on transformed features and combining predictions. They can capture non-linear relationships and interactions that linear models cannot.')
heading('23.2.1 Random Forests', 3, space_before=10)
body('Random forests build many decision trees on bootstrapped samples and aggregate predictions. Each tree uses a random subset of features at each split, decorrelating trees and improving ensemble performance. They are robust, accurate, and provide feature importance measures.')
body('Applying random forests to text requires numeric features: TF-IDF vectors (treating each term as a feature), document-level statistics (length, average word length), and engineered features (keyword presence, category-specific term counts). Random forests on TF-IDF can sometimes outperform linear models on small datasets due to capturing term interactions.')
heading('23.2.2 Gradient Boosting Machines', 3, space_before=10)
body('Gradient boosting builds an ensemble of weak learners (typically shallow trees) sequentially, where each new learner corrects errors of the previous ensemble. XGBoost and LightGBM are highly optimized implementations that often achieve state-of-the-art results on tabular data.')
body('For text classification, gradient boosting requires feature engineering. TF-IDF features can be used directly, or document statistics and keyword-based features can be engineered. Gradient boosting on well-engineered features can outperform linear models, especially when category distinctions depend on feature combinations. Trade-offs include slower training, more hyperparameters, and less direct interpretability.')
heading('23.3 Deep Learning Approaches', 2, space_before=12)
body('Deep learning revolutionized NLP, achieving impressive results on text classification. However, application requires careful consideration of trade-offs between performance, data requirements, compute, and interpretability.')
heading('23.3.1 Word Embeddings and Static Representations', 3, space_before=10)
body('Word embeddings represent words as dense vectors where semantically similar words have similar representations. Pre-trained embeddings (Word2Vec, GloVe, FastText) can be reused or learned as part of a network. Bag-of-embeddings (averaging word embeddings) is simple and often surprisingly effective.')
heading('23.3.2 TextCNN', 3, space_before=10)
body('TextCNN applies 1D convolutions over word embedding sequences to extract local n-gram patterns. Filters slide over the sequence to detect local patterns. A typical architecture embeds words, applies parallel convolutional filters of different widths (2, 3, 4 words), applies max-over-time pooling, concatenates pooled features, and passes through a fully connected layer with softmax.')
heading('23.3.3 LSTM and GRU', 3, space_before=10)
body('RNNs process sequences word by word, maintaining hidden state encoding information from previous words. LSTMs and GRUs address vanishing gradient limitations, allowing capture of longer-range dependencies. Bidirectional RNNs processing in both directions are generally preferred for classification.')
heading('23.3.4 BERT and Transformers', 3, space_before=10)
body('Transformers use self-attention mechanisms to process sequences in parallel, capturing relationships between all word pairs regardless of distance. BERT is pre-trained on massive text using masked language modeling and next sentence prediction, learning rich language representations. For classification, BERT is fine-tuned by adding a classification head on the [CLS] token and training on labeled data.')
table(
    ['Aspect', 'LinearSVC (Current)', 'BERT Fine-tuned', 'Impact on CivicSense'],
    [
        ['Accuracy ceiling', 'Good on small text; may saturate', 'Higher ceiling; transfer learning', 'Marginal gain may not justify cost'],
        ['Training data needed', 'Hundreds per class adequate', 'Hundreds to thousands needed', 'Current corpus adequate for both'],
        ['Compute (training)', 'Minutes on CPU', 'Hours on GPU (or cloud)', 'GPU access needed for BERT'],
        ['Compute (inference)', 'Milliseconds per complaint', '10-50ms on GPU, more on CPU', 'Acceptable for batch; marginal for real-time'],
        ['Interpretability', 'High (feature weights)', 'Lower (attention, gradients)', 'Current approach more explainable'],
        ['Setup complexity', 'Low (scikit-learn only)', 'Higher (PyTorch, Transformers)', 'Simplicity aids reliability'],
        ['Deployment', 'Simple (single pickle file)', 'Model artifacts, GPU dependency', 'Current simpler to deploy'],
        ['Multilingual', 'Requires separate models', 'Multilingual models available', 'BERT enables multilingual from start'],
    ], [1.3, 1.4, 1.5, 1.8], 8.5)
heading('23.4 Practical Recommendations', 2, space_before=12)
body('Based on analysis of available methods and CivicSense requirements, the following recommendations emerge.')
bullet('Use classical methods (TF-IDF + LinearSVC or logistic regression) when training corpus is modest, interpretability is valued, computational resources are limited, and deployment simplicity matters.')
bullet('Consider transformer fine-tuning when larger labeled corpus is available, maximum accuracy is the goal, GPU infrastructure is accessible, or multilingual support is needed from the start.')
bullet('Explore hybrid approaches: use classical methods for initial classification with transformers for difficult cases (confidence-based routing), combine TF-IDF with transformer embeddings as input to gradient boosting, or ensemble multiple models for improved robustness.')
callout('The choice of classification method is an engineering decision depending on application requirements, constraints, and values. For CivicSense, TF-IDF + LinearSVC is well-justified for reliability, interpretability, and simplicity. Future versions may incorporate transformers for use cases where additional accuracy justifies additional complexity.', 'MODEL SELECTION PHILOSOPHY:')

# CH24
print('Inserting Chapter 24')
p = doc.add_paragraph()
p.paragraph_format.page_break_before = True
r = p.add_run('CHAPTER 24: DETAILED USER EXPERIENCE AND INTERFACE DESIGN')
r.font.name = 'Arial'
r.font.size = Pt(16)
r.font.bold = True
r.font.color.rgb = PRIMARY
parent.insert(idx, p._p)
idx += 1

body('CivicSense is designed around user-centered design principles prioritizing accessibility, transparency, efficiency, and consistency. These principles guide every interface decision, from citizen intake form to officer dashboard.')
heading('24.1 User-Centered Design Framework', 2, space_before=12)
heading('24.1.1 Accessibility Standards', 3, space_before=10)
bullet('WCAG 2.1 compliance: Minimum contrast ratios, keyboard navigation, screen reader compatibility through semantic HTML and ARIA attributes')
bullet('Responsive design: Interface adapts to devices from desktop to mobile using flexible grids, fluid images, and media queries')
bullet('Clear language: Avoiding technical jargon, using plain language accessible regardless of education level or technical background')
bullet('Multiple input modalities: Supporting keyboard shortcuts, mouse interactions, and touch gestures for different user preferences and abilities')
bullet('Error tolerance: Clear error messages helping users correct mistakes without frustration; preserving user input so work is not lost on error')
heading('24.1.2 Transparency Principles', 3, space_before=10)
bullet('Clear indication of system vs. human decisions: Users always know when classification is automated and when a human has made a judgment')
bullet('Plain-language explanations: Technical concepts translated into understandable language; confidence explained as "very sure / moderately sure / not sure"')
bullet('Visibility of uncertainty: When model is uncertain, that uncertainty is visible rather than hidden; low-confidence classifications trigger review prompts')
bullet('Feedback loops: Users can provide feedback on system decisions; feedback is logged and considered for improvements')
heading('24.1.3 Efficiency Principles', 3, space_before=10)
bullet('Streamlined intake: Only essential fields required; smart defaults and auto-detection where possible; progressive disclosure of advanced options')
bullet('Quick triage: Officers see key information (priority, category, fraud flag, confidence) at a glance without navigating to detail views')
bullet('Batch operations: When appropriate, multiple complaints can be processed together (batch status updates, batch assignment)')
heading('24.2 Citizen Complaint Intake Experience', 2, space_before=12)
heading('24.2.1 Form Design Patterns', 3, space_before=10)
bullet('Progressive disclosure: Core fields (description, location) always visible; optional fields (photo, room number, sub-location) available but not required')
bullet('Clear labeling: Each field has a descriptive label indicating what information is expected; placeholder text provides example entry')
bullet('Logical grouping: Related fields grouped visually (location fields together, contact/source fields together)')
bullet('Smart defaults: Default choices reduce effort where possible (e.g., pre-filling current date, suggesting likely source based on context)')
heading('24.2.2 Location Input Design', 3, space_before=10)
bullet('Ward selector with recognizable names (not abstract codes)')
bullet('Hierarchical refinement: Ward > Floor > Room > Sub-location, allowing precision without overwhelming detail')
bullet('GPS auto-detect option: Especially useful for mobile users; falls back to ward selection if GPS unavailable')
heading('24.2.3 Photo Upload Experience', 3, space_before=10)
bullet('Drag-and-drop or click-to-upload: Both interaction patterns supported; click-to-upload is more accessible for keyboard users')
bullet('Live preview: Users see photo before submitting, confirming it is the intended image')
bullet('Guidelines communicated: Supported formats, file size limits, expectations communicated before upload')
heading('24.2.4 Submission Confirmation', 3, space_before=10)
bullet('Complaint ID: Unique identifier in CMB-XXXXX format for tracking and reference')
bullet('Summary: Confirmation of what was submitted, including category and priority assigned')
bullet('Explanation: Plain-language explanation of category classification and priority calculation')
bullet('Next steps: What happens next, typical timelines, how to check status')
heading('24.3 Officer Dashboard Design', 2, space_before=12)
heading('24.3.1 Dashboard Layout', 3, space_before=10)
bullet('KPI cards at top: Total complaints, high-priority count, open vs. resolved ratio, average resolution time - visible at a glance')
bullet('Alert panel: Fraud alerts, incident hotspots, cascade warnings displayed prominently with color and iconography')
bullet('Charts: Complaint trends over time by category, priority, and ward; area charts for volume over time; bar charts for category comparison')
bullet('Complaint table: Filterable, sortable, with key fields shown; click expands detail inline or navigates to detail page')
heading('24.3.2 Visual Design System', 3, space_before=10)
bullet('Colors: Primary (#1A2B4C deep navy), secondary accent (#3B5BD2 blue), status colors (High: #D9534F red, Medium: #F0AD4E orange, Low: #5CB85C green)')
bullet('Typography: Arial/Helvetica for body, larger for headings; good readability without excessive size')
bullet('Spacing: Consistent spacing using 8px base unit; adequate white space prevents visual crowding')
bullet('Consistency: Same colors mean same things everywhere; same patterns for similar actions; predictable interactions build trust')
heading('24.3.3 Complaint Detail View', 3, space_before=10)
bullet('Complete information: All submitted data (text, location, photo, source, timestamp) in organized sections')
bullet('Classification results: Category with confidence, key terms that influenced classification, alternative categories considered if uncertain')
bullet('Priority information: Assigned priority, score breakdown by factor, threshold context, override indication if safety axiom applied')
bullet('Fraud assessment: Whether flagged, specific signals detected, explanation, recommended action, photo authenticity if image submitted')
bullet('Duplicate and cluster info: Whether marked duplicate and of what, whether part of incident cluster and which cluster')
bullet('Action panel: Status change, priority override, assign, add notes, resolve, dismiss fraud, mark review complete')
bullet('History: Timeline of all status changes and actions taken on this complaint')
heading('24.4 Explanation Presentation', 2, space_before=12)
heading('24.4.1 Priority Explanation Design', 3, space_before=10)
bullet('Structured template: Initial summary statement, contributing factors with quantified contributions, threshold context, override indication if applicable')
bullet('Design goal: Explanation tells officer why priority was assigned AND what would change the priority, enabling informed judgment and override')
heading('24.4.2 Classification Explanation Design', 3, space_before=10)
bullet('Shows assigned category and confidence, key terms that influenced classification, alternative categories considered and why rejected')
bullet('When confidence is low, explanation emphasizes uncertainty and may suggest review by officer')
heading('24.4.3 Fraud Alert Explanation Design', 3, space_before=10)
bullet('Alert language: "Review recommended" rather than "spam" or "fraud" - flags for review, does not accuse')
bullet('Signal listing: Specific signals detected (URL pattern, token distribution anomaly, keyword mismatch, etc.)')
bullet('Photo consideration: If photo evidence is authentic and meaningful, that is noted as mitigating factor')
heading('24.5 Mobile and Field Officer Experience', 2, space_before=12)
body('Mobile and field use requires special consideration. Officers in the field may view complaints on tablets or phones, and citizens most commonly file from mobile devices. Responsive forms, touch-friendly controls, and GPS auto-detection address these needs.')
heading('24.6 Usability Evaluation Approach', 2, space_before=12)
body('Usability is evaluated through task-completion observation, quantitative metrics (task completion rate, time on task, error rate, satisfaction scores), and feedback collection (surveys, ratings, problem reports). Key focus areas include minimizing steps to file a complaint, reducing time to triage a complaint, reducing errors in common workflows, and measuring user satisfaction.')

# CH25
print('Inserting Chapter 25')
p = doc.add_paragraph()
p.paragraph_format.page_break_before = True
r = p.add_run('CHAPTER 25: PROJECT ORGANIZATION, MANAGEMENT AND INSTITUTIONAL CONTEXT')
r.font.name = 'Arial'
r.font.size = Pt(16)
r.font.bold = True
r.font.color.rgb = PRIMARY
parent.insert(idx, p._p)
idx += 1

heading('25.1 Institutional Profile', 2, space_before=12)
body('Pimpri Chinchwad University (PCU) is a state university established in 2011 under Maharashtra State Government Act No. XXVII of 2011. The university is located in Sate, Maval, Pune - 412106, Maharashtra, India, and serves a diverse academic community across engineering, technology, management, and pharmacy programs.')
two_col([
    ('Institution', 'Pimpri Chinchwad University (PCU)'),
    ('Established', '2011 (Maharashtra State Govt. Act No. XXVII of 2011)'),
    ('Location', 'Sate, Maval, Pune - 412106, Maharashtra, India'),
    ('Department', 'Computer Science & Engineering'),
    ('Program', 'Bachelor of Technology (B.Tech)'),
    ('Academic Year', '2025-2026'),
    ('Project Title', 'CivicSense: AI-Based Citizen Complaint Analyzer'),
    ('Primary Supervisor', 'Dr. S. Deshmukh, Associate Professor, CSE, PCU'),
    ('Co-Supervisor', 'Prof. A. Reddy, Visiting Faculty, IIT Bombay'),
])
heading('25.2 Campus Infrastructure Scope', 2, space_before=12)
body('The university campus includes multiple academic blocks, hostel facilities, dining facilities, and recreational areas, making it a realistic testbed for civic complaint management. Campus scale is large enough to generate meaningful complaint volumes across multiple categories and locations, yet small enough to manage as a realistic pilot deployment.')
bullet('Academic Blocks (A, B, C): Classrooms, laboratories, seminar halls - common sources of classroom and lab infrastructure complaints')
bullet('Administrative Block: University administration offices - provides administrative context and stakeholder access')
bullet('Hostel Complex: Girls Hostel and Boys Hostel - residential facilities generating hostel-related complaints')
bullet('Central Canteen and Cafeteria: Food service facilities - source of canteen and food quality complaints')
bullet('Sports Lawn and Recreation Areas: Athletic facilities - occasional maintenance and safety complaints')
bullet('Main Gates (Entry/Exit): Perimeter security and access points - relevant for campus safety and parking complaints')
heading('25.3 Project Governance Structure', 2, space_before=12)
body('The project operates under supervision of faculty from the Department of Computer Science & Engineering. Dr. S. Deshmukh serves as primary supervisor providing overall project guidance, scope control, and quality assurance. Prof. A. Reddy serves as co-supervisor, providing additional expertise from IIT Bombay and review of research methodology. Project team consists of students of CSE, PCU responsible for all aspects of implementation, testing, documentation, and deployment.')
table(
    ['Role', 'Responsibilities', 'Experience/Background'],
    [
        ['Primary Supervisor', 'Overall guidance, scope, quality, reproducibility requirement', 'Dr. S. Deshmukh, Assoc. Prof., CSE, PCU'],
        ['Co-Supervisor', 'Technical guidance, research methodology review', 'Prof. A. Reddy, Visiting Faculty, IIT Bombay'],
        ['Project Team', 'Implementation, testing, documentation, deployment', 'B.Tech Students, CSE, PCU'],
    ], [1.5, 2.6, 1.9], 9)
heading('25.4 Development Methodology', 2, space_before=12)
body('The project follows an iterative development approach. The system is built and improved in iterations with continuous testing, regular review with supervisors, documentation created alongside implementation, and emphasis on reproducibility throughout. Reproducibility is treated as a first-class requirement, not an afterthought: data generation uses deterministic seeds, model training produces documented artifacts, system configuration is captured, and evaluation procedures are documented in detail.')
heading('25.5 Timeline and Milestones', 2, space_before=12)
table(
    ['Milestone', 'Timeline', 'Key Activities', 'Deliverables'],
    [
        ['Project Initiation', 'Aug 2025 (Week 1-2)', 'Literature review, requirements, planning', 'Project proposal, initial plan'],
        ['Phase 1 Development', 'Sep-Nov 2025 (Week 3-12)', 'Traditional pipeline implementation', 'Working traditional pipeline'],
        ['Phase 1 Evaluation', 'Nov-Dec 2025 (Week 13-14)', 'Testing, evaluation, bug fixing', 'Test reports, evaluation results'],
        ['Phase 1 Documentation', 'Dec 2025 (Week 15-16)', 'Comprehensive Phase 1 documentation', 'Phase 1 report'],
        ['Phase 2 Development', 'Jan-Mar 2026 (Week 17-24)', 'NCM-Net framework development', 'Working NCM-Net system'],
        ['Phase 2 Evaluation', 'Mar 2026 (Week 25-26)', 'Advanced testing, validation', 'Advanced test reports'],
        ['Phase 2 Documentation', 'Mar-Apr 2026 (Week 27-28)', 'Comprehensive Phase 2 documentation', 'Phase 2 report'],
        ['Integration', 'Apr 2026 (Week 29-30)', 'Combine Phase 1 and Phase 2', 'Master report'],
        ['Final Review & Submission', 'May 2026 (Week 31-32)', 'Final review, formatting, submission', 'Final project submission'],
    ], [1.2, 1.4, 2.0, 1.5], 8.5)
heading('25.6 Work Distribution and Skill Mapping', 2, space_before=12)
table(
    ['Skill Area', 'Application in Project', 'Importance'],
    [
        ['Python Programming', 'Primary implementation language for all modules', 'Essential - all components in Python'],
        ['Machine Learning', 'Classification, clustering, fraud, conformal, boosting', 'Core - intelligent triage is central'],
        ['Natural Language Processing', 'Text preprocessing, TF-IDF, classification, embeddings', 'Essential - text is primary input'],
        ['Web Development (Flask)', 'REST API design, dashboard templates, route handling', 'Essential - user-facing platform'],
        ['Database (SQLite)', 'Data modeling, persistence, queries, migrations', 'Essential - all data stored'],
        ['Testing & QA', 'Smoke tests, unit evaluation, coverage tracking', 'Essential - ensures reliability'],
        ['Documentation', 'Technical writing, report structure, diagrams', 'Essential - communicates work'],
        ['UI/UX Design Principles', 'Dashboard layout, form design, explanation presentation', 'Important - drives adoption'],
        ['Research Methodology', 'Literature review, gap analysis, evaluation design', 'Important - establishes credibility'],
        ['Project Management', 'Timeline, coordination, deliverables tracking', 'Important - ensures completion'],
    ], [1.4, 2.6, 2.0], 9)
heading('25.7 Risk Management and Mitigation', 2, space_before=12)
table(
    ['Risk', 'Probability', 'Impact', 'Mitigation Strategy'],
    [
        ['Transformer libraries unavailable', 'Medium', 'High - cannot fine-tune BERT', 'Fall back to TF-IDF + LinearSVC; document limitation'],
        ['Small training corpus limits accuracy', 'High', 'Medium - lower accuracy', 'Document honestly; compare with expected 93%'],
        ['Scope creep expands project beyond time', 'Medium', 'High - incomplete work', 'Clear scope definition; regular review'],
        ['Time constraints compress remaining work', 'Medium', 'Medium - rushed final stages', 'Iterative approach; buffer in schedule'],
        ['Technical bugs in production code', 'Medium', 'Medium - incorrect results', 'Testing throughout; smoke test suite'],
        ['Incomplete or unclear documentation', 'Low', 'High - poor evaluation', 'Documentation alongside implementation'],
        ['Data quality issues in corpus', 'Low', 'Medium - biased results', 'Careful corpus design; transparent about synthetic'],
        ['Difficulty demonstrating system works', 'Low', 'High - poor evaluation', 'Smoke test ensures demonstrable system'],
    ], [1.0, 0.8, 0.8, 3.2], 8.5)
heading('25.8 Ethical Considerations in Project Execution', 2, space_before=12)
body('Academic integrity is maintained through original implementation, proper attribution of the base paper and other sources, honest reporting of results including limitations and failures, and no plagiarism - all content is original or properly attributed. Reproducibility is treated as a requirement to ensure results are verifiable.')
body('Responsible AI development is practiced by being transparent about what the system can and cannot do, ensuring the system assists rather than replaces human decision-making, considering privacy implications (demonstration uses synthetic data), and acknowledging potential biases in limitations. Social responsibility is demonstrated through beneficial application design, accessibility consideration for diverse users, use of open-source tools, and documentation that enables others to learn and build upon the work.')

# CH26
print('Inserting Chapter 26')
p = doc.add_paragraph()
p.paragraph_format.page_break_before = True
r = p.add_run('CHAPTER 26: COMPREHENSIVE EVALUATION METHODOLOGY AND STATISTICAL ANALYSIS')
r.font.name = 'Arial'
r.font.size = Pt(16)
r.font.bold = True
r.font.color.rgb = PRIMARY
parent.insert(idx, p._p)
idx += 1

heading('26.1 Evaluation Philosophy', 2, space_before=12)
body('Evaluation is designed around three principles: honesty (report actual measured numbers, not aspirational targets), reproducibility (document exactly what was evaluated, on what data, with what procedure), and comprehensiveness (evaluate technical performance, functional completeness, usability, robustness, and practical value).')
heading('26.2 Corpus Design Principles', 2, space_before=12)
body('The demonstration corpus is carefully designed to enable meaningful evaluation. Unlike many projects that evaluate on unclear data, CivicSense uses a designed corpus with known ground truth, injected scenarios, and reproducible generation.')
table(
    ['Design Aspect', 'Approach', 'Purpose'],
    [
        ['Known ground truth', 'Every complaint has assigned category, expected priority, labels', 'Enables quantitative metrics'],
        ['Injected scenarios', 'Fraud, duplicates, clusters injected with known parameters', 'Enables evaluation of these features'],
        ['Reproducible generation', 'Deterministic seed; same seed produces same corpus', 'Enables exact replication'],
        ['Coverage diversity', 'All categories, wards, priorities, lengths represented', 'Reduces bias from single scenario'],
        ['Realistic parameters', 'Counts, distributions match expected real-world patterns', 'Enables meaningful extrapolation'],
        ['Scalable design', 'Parse + generate structure allows larger corpus', 'Enables future larger evaluation'],
    ], [1.3, 2.3, 2.1], 9)
heading('26.3 Metric Selection Rationale', 2, space_before=12)
body('Metrics are selected based on what they measure and how relevant that is to system goals. Accuracy and F1 capture classification correctness, confusion matrices reveal specific errors, priority distribution analysis validates score behavior, duplicate and fraud detection rates validate those specific features, and latency and throughput validate operational viability.')
heading('26.3.1 Accuracy and F1', 3, space_before=10)
body('Accuracy measures overall correctness: fraction of complaints where predicted category matches true category. However, accuracy can be misleading with imbalanced classes. F1 score (harmonic mean of precision and recall) combines both concerns into a single metric per class. Macro F1 averages per-class F1 equally, treating all classes equally regardless of frequency. Weighted F1 averages per-class F1 weighted by class frequency, reflecting overall distribution. Both are reported to give a complete picture.')
heading('26.3.2 Confusion Matrix Analysis', 3, space_before=10)
body('Confusion matrices reveal which classes are confused with each other. Each cell (i, j) shows the count of items of true class i predicted as class j. High values off-diagonal indicate specific confusions to investigate. For civic complaints, certain confusions are expected (related categories), and understanding them helps interpret and improve the classifier.')
heading('26.3.3 Cross-Validation', 3, space_before=10)
body('Stratified k-fold cross-validation (k=5) provides robust estimates. The dataset is split into 5 folds maintaining class distribution. For each fold, training on 4 folds and testing on the held-out fold produces an estimate. Results are aggregated as mean and standard deviation across folds. Cross-validation reduces variance due to a particular train-test split choice and reveals performance stability across different data subsets. It is more robust than a single split, which is especially important with modest dataset sizes.')
heading('26.3.4 Priority Evaluation', 3, space_before=10)
body('Priority evaluation is more qualitative than classification, as priority is a derived score rather than a predicted label. Priority distribution analysis examines the distribution of assigned priorities, score breakdown analysis examines the contribution of each factor, and scenario-based evaluation tests specific priority scenarios (emergencies, routine cases, edge cases). Explanation quality is assessed by whether explanations are clear, accurate, and useful.')
heading('26.3.5 Duplicate and Fraud Detection Evaluation', 3, space_before=10)
body('Duplicate detection is evaluated on detection rate (of known duplicate pairs, how many detected; target 9/9 = 100%) and false positive rate (of non-duplicates, how many incorrectly flagged; target 0/182 = 0%). Fraud detection is evaluated on detection rate (of 8 injected fraud, how many flagged; target 8/8 = 100%) and false positive rate (of legitimate complaints, how many incorrectly flagged; target 0/192 = 0%).')
heading('26.3.6 Clustering Evaluation', 3, space_before=10)
body('Clustering evaluation is primarily qualitative, as clustering is an unsupervised process without definitive ground truth. The system is evaluated on whether it forms clusters from injected complaints, whether clusters contain the expected complaints, whether clusters are sensible (same issue, same area), and whether clusters appear correctly in the dashboard.')
heading('26.4 Statistical Validity Considerations', 2, space_before=12)
body('Several statistical considerations affect interpretation of results. Sample size (200 complaints, 5 categories) provides reasonable estimates but with some uncertainty. Cross-validation reduces variance from split choice. Corpus bias (synthetic, may not perfectly represent real distributions) is acknowledged. Results may not generalize to other contexts; this is explicitly noted as a limitation.')
body('Threats to validity include internal validity (evaluation measures what it claims - supported by controlled scenarios), external validity (results may not generalize - acknowledged as limitation), construct validity (metrics capture intended constructs - supported by standard metrics), and conclusion validity (conclusions supported by evidence - supported by honest reporting).')
body('Confidence in results increases when multiple evaluation approaches (aggregate metrics, per-class analysis, confusion matrices, scenario evaluation, manual review) converge on similar conclusions. This multi-faceted approach provides robust, well-rounded assessment of system capabilities and limitations.')
heading('26.5 Results Summary', 2, space_before=12)
table(
    ['Evaluation Area', 'Primary Metric', 'Result', 'Interpretation'],
    [
        ['Classification', 'Accuracy', '82.19% (5-fold CV)', 'Strong baseline; gap vs 93% expected for scale'],
        ['Per-Class F1', 'Macro F1', '82.8% (balanced)', 'No category severely underperforming'],
        ['Priority', 'Distribution match', 'Matches expected', 'Formula behaves sensibly'],
        ['Duplicate Detection', 'Detection rate', '9/9 = 100%', 'Excellent on injected scenario'],
        ['Fraud Detection', 'Detection rate', '8/8 = 100%', 'Excellent on injected; 0 false positives'],
        ['Clustering', 'Cluster formation', '6/6 clusters', 'Clustering useful; shows patterns'],
        ['Digest Quality', 'Consistency check', 'Consistent, complete', 'Template produces reliable digests'],
        ['Latency', 'Round-trip time', '<200ms typical', 'Operationally viable; no bottleneck'],
        ['Test Coverage', 'Smoke test', 'All checks pass', 'System functionally complete'],
    ], [1.2, 1.3, 1.6, 2.0], 8.5)
callout('A rigorous evaluation methodology is as important as the system itself. By evaluating honestly on a designed corpus, reporting actual numbers with limitations, and enabling replication through reproducibility, the project establishes credibility and provides a foundation for future work to build upon and compare against.', 'EVALUATION PHILOSOPHY:')

# CH27
print('Inserting Chapter 27')
p = doc.add_paragraph()
p.paragraph_format.page_break_before = True
r = p.add_run('CHAPTER 27: CONCLUSION AND FINAL REMARKS')
r.font.name = 'Arial'
r.font.size = Pt(16)
r.font.bold = True
r.font.color.rgb = PRIMARY
parent.insert(idx, p._p)
idx += 1

heading('27.1 Summary of Accomplishments', 2, space_before=12)
heading('27.1.1 Phase 1: Traditional Complaint Triage Pipeline', 3, space_before=10)
bullet('Base paper implementation: Complete implementation of the base papers complaint triage pipeline, including text preprocessing, category classification, duplicate detection, near-duplicate clustering, priority assignment, and fraud detection.')
bullet('Five meaningful extensions: Fraud detection with statistical and content signals, near-duplicate clustering for incident pattern surfacing, explainable AI throughout with plain-language explanations, structured reporting with weekly digests and PDF/Excel export, and reproducible evaluation with controlled demonstration corpus.')
bullet('Measurable results: Demonstrated 82.19% classification accuracy on controlled 200-complaint corpus, complete duplicate and fraud detection on injected scenarios, and comprehensive evaluation including confusion matrices and per-class analysis.')
bullet('Working system: Fully functional dashboard, REST API, and admin interface providing practical citizen complaint intake and officer triage tools.')
heading('27.1.2 Phase 2: NCM-Net Advanced Framework', 3, space_before=10)
bullet('Four novel research pillars: AG-CMA cross-modal alignment, Conformal Prediction with certified coverage, Neuro-Symbolic Safety Layer with 100% zero-miss recall, and ST-ICK spatio-temporal cascade kernel.')
bullet('Mathematical formulations: Complete mathematical foundations documented with theorems, proofs, complexity analyses, and parameter guidelines.')
bullet('Computer vision and GIS: Advanced image analysis with AG-CMA gating and cross-modal routing, plus comprehensive GIS integration with 13 high-precision coordinates and Google Maps integration.')
bullet('Comprehensive testbed: 200-complaint demonstration corpus with 6 categories, 13 wards, 140 officers, 30-day temporal span, and realistic complaint patterns.')
bullet('Published results: Benchmark study (Table 85) showing NCM-Net achieves 83.08% accuracy with certified 90% coverage and 100% safety recall across 5 papers, with ablation study showing contribution of each pillar.')
bullet('Five detailed case studies: Realistic walkthroughs demonstrating system response to electrical emergency, water leak, fraudulent blank-image complaint, cascade incident, and fraud detection.')
bullet('Production-ready deployment: Complete API reference, database schema with migration guides, deployment guide, testing strategy, and operational configuration.')
heading('27.2 Innovation and Differentiation', 2, space_before=12)
body('CivicSense differentiates from existing systems through several dimensions:')
table(
    ['Dimension', 'Conventional Civic Systems', 'CivicSense (NCM-Net)'],
    [
        ['ML approach', 'Heuristic rules or black-box classifiers', 'Certified ML: conformal + neuro-symbolic guarantees'],
        ['Safety assurance', 'Feature flags or keyword overrides', 'FOL axioms: formal correctness guarantees'],
        ['Image handling', 'Manual review or no automation', 'AG-CMA gate + cross-modal alignment'],
        ['Duplicate detection', 'Exact match or simple similarity', 'Weighted multi-feature similarity + ward scoping'],
        ['Geographic', 'Static ward assignments', 'GPS auto-detection + 13-coordinate GIS + Google Maps'],
        ['Cascade handling', 'No cascade detection', 'ST-ICK kernel with 2-hour cascade window'],
        ['Explanations', 'Rare or technical', 'Mandatory plain-language everywhere'],
        ['Batch operations', 'Manual one-by-one', '1-click batch with audit trail'],
        ['Certification', 'None', 'Formal certification framework'],
        ['Deployment', 'Often custom/unique', 'Reproducible pipeline, documented APIs'],
    ], [1.2, 2.3, 2.3], 8.5)
heading('27.3 Honest Assessment of Limitations', 2, space_before=12)
body('No system is perfect, and honest assessment of limitations is essential for responsible deployment and clear-eyed future planning. The limitations below are acknowledged not as failures, but as known boundaries within which the system operates, providing a clear picture of what the system can and cannot do.')
heading('27.3.1 Data Limitations', 3, space_before=10)
bullet('Demonstration corpus is synthetic: Generated systematically rather than drawn from real complaint history, so real-world distributions may differ.')
bullet('Corpus size is modest (200 complaints): Sufficient for meaningful evaluation and to demonstrate system behavior, but not large enough to claim production-ready performance across all categories.')
bullet('No multilingual text in current corpus: Built for English; real campuses serve multilingual populations.')
bullet('No real-world performance data: Evaluation is on designed corpus; actual deployment performance unknown until deployed in production.')
heading('27.3.2 Technical Limitations', 3, space_before=10)
bullet('Classification accuracy is good but not perfect: 82.19% means approximately 1 in 6 complaints classified incorrectly; misclassifications are typically to related categories.')
bullet('Fraud detection is scenario-based: Tested on injected scenarios; real-world fraud patterns may differ and require adaptation.')
bullet('Duplicate detection relies on TF-IDF similarity: True semantic duplicates expressed very differently may not be detected; going beyond TF-IDF is future work.')
bullet('Explainability is template-based for priority: Priority explanations are structured but formula-based; deeper explanations are future work.')
bullet('No deployment at scale and no long-term reliability data available yet; operational characteristics under sustained load unknown.')
bullet('Geographic coverage limited to PCU campus: 13 coordinates cover campus facilities; extension to broader city requires more extensive data.')
heading('27.3.3 Evaluation Limitations', 3, space_before=10)
bullet('Evaluation corpus is designed rather than organic: Designed for evaluation, so may not capture full diversity and difficulty of real complaints.')
bullet('No user study: Usability claims based on design principles, not measured user behavior; formal usability testing is future work.')
bullet('No A/B testing or live comparison: Cannot directly compare system-assisted triage with previous manual process.')
heading('27.4 Future Work', 2, space_before=12)
body('Future work spans technical, functional, research, and deployment dimensions, building on the foundation established by CivicSense.')
heading('27.4.1 Technical Enhancements', 3, space_before=10)
bullet('Transformer integration: Fine-tuning DistilBERT or other distilled models for classification; balance accuracy improvement against compute cost and operational complexity.')
bullet('Multilingual support: Adding Marathi and Hindi using multilingual BERT or similar, reflecting reality of Indian campuses serving diverse linguistic populations.')
bullet('Voice input: Integrating speech-to-text for voice complaint submission; accessibility and convenience benefit.')
bullet('Advanced computer vision: More sophisticated image analysis using modern deep learning for defect detection, damage assessment, anomaly identification.')
bullet('Real-time streaming analytics: Real-time dashboards and alerts for monitoring complaint flow as it happens.')
heading('27.4.2 Functional Enhancements', 3, space_before=10)
bullet('IoT integration: Connecting to campus sensors (water, electricity, fire, occupancy) for proactive monitoring and automated incident detection.')
bullet('Mobile application: Native apps for citizens and officers with push notifications, camera integration, offline capability, location awareness.')
bullet('Workflow automation: Automated assignment, escalation, SLA tracking, resolution workflows reducing manual coordination burden.')
bullet('Predictive analytics: Forecasting complaint trends by time, location, category for proactive resource allocation and prevention.')
bullet('Citizen feedback loop: Collecting satisfaction feedback on resolution, closing the loop with citizens, building trust through responsiveness.')
heading('27.4.3 Research and Publication', 3, space_before=10)
bullet('Publication: Preparing NCM-Net contributions for peer-reviewed venue (AI for social good, responsible AI, civic technology conferences).')
bullet('Extended evaluation: Evaluating on larger, more diverse, ideally real datasets to validate generalizability.')
bullet('Comparative studies: Systematic comparison with other civic AI approaches on common benchmarks.')
bullet('HCI studies: Studying how officers and citizens actually use system, identifying usability issues and adoption barriers.')
bullet('Formal verification: Extending neuro-symbolic framework to broader axioms, potentially exploring automated axiom learning or verification.')
heading('27.5 Closing Remarks', 2, space_before=12)
body('The CivicSense project represents a significant step toward AI-powered civic technology that is both intelligent and trustworthy. It demonstrates that academic research can be translated into practical, working systems addressing real-world problems, and that rigorous engineering practices (reproducibility, testing, honest evaluation, comprehensive documentation) produce systems worthy of trust.')
body('The project contributes to academic knowledge through the NCM-Net framework and its four research pillars, each providing novel algorithmic approaches to problems in civic AI. It contributes practical value through a working system that could genuinely improve complaint handling at university campuses and, scaled, at municipal levels. And it contributes to responsible AI practice through transparent documentation, honest limitation reporting, and community-oriented openness.')
body('The team expresses gratitude to all who have contributed to and supported this project, including supervisors Dr. S. Deshmukh and Prof. A. Reddy, the Department of Computer Science & Engineering at Pimpri Chinchwad University, and the broader open-source community whose tools and libraries made this work possible.')
body('CivicSense stands as a demonstration that AI for civic good is not just aspirational - it can be practical, trustworthy, and beneficial today. The journey from this point involves real-world deployment, continuous improvement, and expansion to serve the communities that need it most.')
callout('CivicSense demonstrates that AI-powered civic systems can be both highly accurate and mathematically trustworthy. The integration of conformal prediction and neuro-symbolic reasoning addresses a critical gap between experimental machine learning and deployment-ready governance technology. We believe this work provides a blueprint for future smart campus and smart city platforms.', 'FINAL THOUGHT:')

doc.save("Project_Report_Master.docx")
print('DONE! Saved Project_Report_Master.docx')
print('Total paragraphs: %d' % len(doc.paragraphs))
print('Total tables: %d' % len(doc.tables))
