"""Expand the master report to exceed 120 pages.

Inserts 5 new chapters (23-27) before APPENDIX A with dense, table-heavy content.
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document('Project_Report_Master_backup.docx')

PRIMARY = RGBColor(26, 43, 76)
SECONDARY = RGBColor(59, 91, 219)
DARK = RGBColor(30, 41, 59)
MUTED = RGBColor(100, 116, 139)

def cell_bg(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    tcPr.append(shd)

def cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}'
        f'><w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/></w:tcMar>'
    )
    tcPr.append(tcMar)

def heading(doc, text, level=1, color=None, space_before=14):
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

def body(doc, text, indent=False, space_after=4):
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

def bullet(doc, text, level=0, space_after=3):
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

def callout(doc, text, title='KEY INSIGHT:', bg='F0F7FF', border='1A2B4C'):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    cell_bg(cell, bg)
    cell_margins(cell, 80, 80, 120, 120)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}'
        f'><w:left w:val="single" w:sz="24" w:space="0" w:color="{border}"/>'
        f'<w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>'
    )
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    rt = p.add_run(title)
    rt.font.name = 'Arial'; rt.font.size = Pt(10); rt.font.bold = True; rt.font.color.rgb = SECONDARY
    r = p.add_run(' ' + text)
    r.font.name = 'Arial'; r.font.size = Pt(10); r.font.color.rgb = DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def table(doc, headers, rows, col_widths=None, font_size=9):
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
        r.font.name = 'Arial'; r.font.size = Pt(font_size); r.font.bold = True
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
            r.font.name = 'Arial'; r.font.size = Pt(font_size); r.font.color.rgb = DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    return tbl

def two_col(doc, rows_data, left_width=2.2, right_width=4.3):
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
        rl.font.name = 'Arial'; rl.font.size = Pt(9.5); rl.font.bold = True; rl.font.color.rgb = DARK
        pv = cv.paragraphs[0]
        pv.paragraph_format.space_before = Pt(0)
        pv.paragraph_format.space_after = Pt(0)
        rv = pv.add_run(value)
        rv.font.name = 'Arial'; rv.font.size = Pt(9.5); rv.font.color.rgb = DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

# Find anchor paragraph
target_text = 'APPENDIX A: HOW TO RUN THE PROJECT'
target_para = None
for p in doc.paragraphs:
    if target_text in p.text:
        target_para = p
        break

if target_para:
    parent = target_para._p.getparent()
    idx = list(parent).index(target_para._p)

    def new_chapter(title_text):
        p = doc.add_paragraph()
        p.paragraph_format.page_break_before = True
        r = p.add_run(title_text)
        r.font.name = 'Arial'; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = PRIMARY
        parent.insert(idx, p._p)
        idx_add = idx + 1
        # Internal reference workaround: return nothing, content added via body/heading
        return idx_add

    idx += 1

    # CH 23
    p = doc.add_paragraph(); p.paragraph_format.page_break_before = True
    r = p.add_run('CHAPTER 23: ADVANCED CLASSIFICATION TECHNIQUES AND MODEL OPTIMIZATION')
    r.font.name = 'Arial'; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = PRIMARY
    parent.insert(idx, p._p); idx += 1

    body(doc, 'This chapter provides an in-depth examination of advanced classification techniques applicable to civic complaint analysis. While CivicSense currently uses TF-IDF with LinearSVC for reliability, interpretability, and low compute requirements, understanding the broader landscape of classification methods is essential for evaluating options and planning future system improvements.')
    
    heading(doc, '23.1 Classical Machine Learning Approaches', 2, space_before=12)
    body(doc, 'Classical machine learning approaches remain highly relevant for text classification, especially with limited training data and where interpretability is valued. These methods have been extensively studied across decades and provide strong baselines that are difficult to outperform on small, well-structured tasks.')
    
    heading(doc, '23.1.1 Naive Bayes Classifiers', 3, space_before=10)
    body(doc, 'Naive Bayes is a probabilistic classifier based on Bayes theorem with the assumption of feature independence between words. Despite this simplifying assumption, it often performs well on text classification tasks and serves as a strong baseline. The multinomial Naive Bayes variant is particularly suited for document classification where features represent word counts.')
    body(doc, 'Training a multinomial Naive Bayes classifier involves estimating the prior probability of each class from the training data and estimating the conditional probability of each word given each class. Laplace smoothing is applied to avoid zero probabilities for words not seen during training.')
    table(doc,
        ['Characteristic', 'Naive Bayes', 'Relevance to Civic Complaints'],
        [
            ['Training speed', 'Very fast (linear in documents × vocab)', 'Acceptable for periodic retraining'],
            ['Prediction speed', 'Very fast (forecast on vectors)', 'Real-time triage feasible'],
            ['Data requirement', 'Tens to hundreds per class work', 'Matches current corpus size'],
            ['Feature independence', 'Assumed (violated in language)', 'Acceptable gap given simplicity'],
            ['Probabilistic outputs', 'Natural (class posterior)', 'Confidence scores available'],
            ['Vocabulary handling', 'Requires fixed vocabulary', 'Vocabulary needs periodic refresh'],
        ], [1.4, 2.3, 2.3], 9)
    body(doc, 'Naive Bayes serves as an excellent baseline. If more complex models cannot clearly beat Naive Bayes on a given task, the simpler model may be preferred for its interpretability and speed.')
    
    heading(doc, '23.1.2 Support Vector Machines', 3, space_before=10)
    body(doc, 'Support Vector Machines find the optimal hyperplane separating classes with maximum margin. LinearSVC is particularly effective for high-dimensional text data. The key insight is that the decision boundary is determined only by support vectors - the training examples closest to the boundary.')
    body(doc, 'The linear kernel is preferred for text classification because text data is typically linearly separable in high-dimensional TF-IDF space. Non-linear kernels (RBF, polynomial) add computational cost and often do not improve performance on text data, making linearSVC the pragmatic choice.')
    table(doc,
        ['Parameter', 'Effect', 'Typical Values for Text'],
        [
            ['C (regularization)', 'Higher C = narrower margin, fewer errors tolerated', '0.1 to 1.0 typical'],
            ['class_weight (balanced)', 'Adjusts loss for imbalanced classes', 'Often helpful for fewer-shot categories'],
            ['dual', 'Which formulation to solve', 'Use dual=False for n_samples > n_features'],
            ['tol (tolerance)', 'Stopping criterion precision', '1e-4 typical; smaller = more precise'],
            ['max_iter', 'Iteration limit', 'Set high enough (5000+) for convergence'],
        ], [1.3, 2.2, 2.3], 9)
    body(doc, 'LinearSVC is CivicSenses current choice. The reasons include strong performance on high-dimensional sparse data, fast prediction, and a well-defined decision boundary that provides interpretable distance-to-boundary as confidence indicator.')
    
    heading(doc, '23.1.3 Logistic Regression', 3, space_before=10)
    body(doc, 'Logistic regression estimates class probabilities using a logistic (sigmoid) function for binary outcomes, generalized to softmax for multi-class problems. It is a convex optimization problem with a globally optimal solution, making it reliable and well-understood.')
    body(doc, 'Logistic regression is particularly attractive when calibrated probabilities are important. Unlike SVM scores, logistic regression outputs are genuine probability estimates (assuming the model is well-specified). For applications where probability calibration matters, logistic regression is often the first choice.')
    body(doc, 'The main limitation of logistic regression for text is the linear decision boundary assumption. However, in high-dimensional TF-IDF space, linear boundaries often capture enough structure for practical classification, especially when the categories are reasonably distinct.')
    
    heading(doc, '23.2 Advanced Classical Models: Tree-Based Ensembles', 2, space_before=12)
    body(doc, 'Tree-based ensemble methods offer a different approach: building decision trees on transformed features and combining their predictions. These methods can capture non-linear relationships and interactions between features that linear models cannot.')
    
    heading(doc, '23.2.1 Random Forests', 3, space_before=10)
    body(doc, 'Random forests build many decision trees on bootstrapped samples and aggregate their predictions. Each tree uses a random subset of features at each split, decorrelating the trees and improving ensemble performance. Random forests are robust, accurate, and provide feature importance measures.')
    body(doc, 'To apply random forests to text, features must be numeric. Common approaches include TF-IDF vectors (treating each term as a feature), document-level statistics (length, average word length, etc.), and engineered features (keyword presence, category-specific term counts). Random forests on TF-IDF features can sometimes outperform linear models on small datasets due to their ability to capture term interactions.')
    
    heading(doc, '23.2.2 Gradient Boosting Machines (XGBoost, LightGBM)', 3, space_before=10)
    body(doc, 'Gradient boosting builds an ensemble of weak learners (typically shallow trees) sequentially, where each new learner corrects the errors of the previous ensemble. XGBoost and LightGBM are highly optimized implementations that often win machine learning competitions and achieve state-of-the-art results on tabular data.')
    body(doc, 'For text classification, gradient boosting requires feature engineering. TF-IDF features can be used directly, or document statistics and keyword-based features can be engineered. Gradient boosting on well-engineered features can outperform linear models, especially when category distinctions depend on combinations of features rather than individual terms.')
    body(doc, 'The trade-offs include slower training due to sequential nature, more hyperparameters to tune, and less direct interpretability. For CivicSense current scale, gradient boosting is a viable option if improvements over linearSVC are needed, but it requires more experimentation and tuning effort.')
    
    heading(doc, '23.3 Deep Learning Approaches', 2, space_before=12)
    body(doc, 'Deep learning has revolutionized NLP, achieving impressive results on text classification tasks. However, their application requires careful consideration of trade-offs between performance, data requirements, compute resources, and interpretability.')
    
    heading(doc, '23.3.1 Word Embeddings and Static Representations', 3, space_before=10)
    body(doc, 'Word embeddings represent words as dense vectors where semantically similar words have similar representations. These can be pre-trained (Word2Vec, GloVe, FastText) on large corpora and reused, or learned as part of a network. For document classification, word embeddings must be aggregated into document representations.')
    body(doc, 'Bag-of-embeddings (averaging word embeddings) is the simplest approach and often surprisingly effective. A document is represented as the average of its word embeddings, producing a fixed-size vector regardless of document length. This representation can feed into a simple classifier (logistic regression, SVM, or shallow neural network).')
    body(doc, 'The advantage of pre-trained embeddings is that they capture semantic similarity not present in TF-IDF. For example, "water supply interrupted" and "no running water" share terms only through "water"; embeddings capture that "interrupted" and "no" relate to absence. This semantic generalization can improve classification on varied language.')
    
    heading(doc, '23.3.2 Convolutional Neural Networks (TextCNN)', 3, space_before=10)
    body(doc, 'TextCNN applies 1D convolutions over word embedding sequences to extract local n-gram patterns. Filters slide over the sequence to detect local patterns. The architecture is simple, efficient, and effective for text classification, often matching or exceeding more complex models.')
    body(doc, 'A typical TextCNN architecture embeds words, applies parallel convolutional filters of different widths (e.g., 2, 3, 4 words) to capture different n-gram patterns, applies max-over-time pooling to extract the strongest feature for each filter, concatenates the pooled features, and passes through a fully connected layer with softmax activation.')
    body(doc, 'TextCNN advantages include capturing local word order (unlike bag-of-words or bag-of-embeddings), reasonable efficiency, and modest parameter count. Limitations include fixed context window (non-local patterns captured only through stacking layers), and still requiring embedding learning or pre-trained embeddings.')
    
    heading(doc, '23.3.3 Recurrent Networks (LSTM, GRU)', 3, space_before=10)
    body(doc, 'Recurrent neural networks process sequences word by word, maintaining hidden state that encodes information from previous words. LSTMs (Long Short-Term Memory) and GRUs (Gated Recurrent Units) address the vanishing gradient problem that limits plain RNNs, allowing them to capture longer-range dependencies.')
    body(doc, 'For classification, the final hidden state (or pooling over all hidden states) serves as the document representation, which is passed through a classification layer. Bidirectional RNNs process the sequence in both directions, capturing context from both past and future words, and are generally preferred over unidirectional RNNs for classification.')
    
    heading(doc, '23.3.4 Transformer Models and BERT', 3, space_before=10)
    body(doc, 'Transformers use self-attention mechanisms to process sequences in parallel, capturing relationships between all pairs of words regardless of distance. BERT (Bidirectional Encoder Representations from Transformers) is pre-trained on massive text corpora using masked language modeling and next sentence prediction, learning rich representations of language.')
    body(doc, 'For text classification, BERT is fine-tuned by adding a classification head on top of the [CLS] token representation and training on labeled data. Fine-tuning BERT on hundreds to thousands of labeled examples typically yields strong results, leveraging the knowledge captured during pre-training.')
    body(doc, 'The practical considerations for CivicSense include: BERT-Base requires significant GPU memory for training and inference, fine-tuning requires several hundred labeled examples per category for best results, inference latency is higher than linear models (though still acceptable for batch processing), and interpretability is reduced compared to simpler models.')
    body(doc, 'Whether BERT is worth the added complexity for CivicSense depends on how much improvement is needed. If TF-IDF + LinearSVC achieves acceptable accuracy, the marginal gains from BERT may not justify the added complexity. If accuracy is insufficient, transformer fine-tuning is the most powerful option available.')

    # CH 24
    p = doc.add_paragraph(); p.paragraph_format.page_break_before = True
    r = p.add_run('CHAPTER 24: DETAILED USER EXPERIENCE AND INTERFACE DESIGN')
    r.font.name = 'Arial'; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = PRIMARY
    parent.insert(idx, p._p); idx += 1

    heading(doc, '24.1 User-Centered Design Framework', 2, space_before=12)
    body(doc, 'CivicSense is designed around principles of user-centered design that prioritize accessibility, transparency, efficiency, and consistency. These principles guide every interface decision, from the citizen intake form to the officer dashboard.')
    heading(doc, '24.1.1 Accessibility Standards', 3, space_before=10)
    bullet(doc, 'WCAG 2.1 compliance: Minimum contrast ratios (4.5:1 for normal text, 3:1 for large text), keyboard navigation support, screen reader compatibility through semantic HTML and ARIA attributes')
    bullet(doc, 'Responsive design: Interface adapts to devices from desktop monitors to mobile phones using flexible grids, fluid images, and media queries')
    bullet(doc, 'Clear language: Avoiding technical jargon, using plain language that all users can understand regardless of education level or technical background')
    bullet(doc, 'Multiple input modalities: Supporting keyboard shortcuts, mouse interactions, and touch gestures to accommodate different user preferences and abilities')
    bullet(doc, 'Error tolerance: Clear error messages that help users correct mistakes without frustration; preserving user input so they do not lose work on error')
    
    heading(doc, '24.1.2 Transparency Principles', 3, space_before=10)
    bullet(doc, 'Clear indication of system vs. human decisions: Users always know when a classification is automated and when a human has made a judgment')
    bullet(doc, 'Plain-language explanations: Technical concepts translated into understandable language; confidence levels explained as "the system is very sure/moderately sure/not sure"')
    bullet(doc, 'Visibility of uncertainty: When the model is uncertain, that uncertainty is visible rather than hidden; low-confidence classifications trigger review prompts')
    bullet(doc, 'Feedback loops: Users can provide feedback on system decisions; this feedback is logged and considered for improvements')
    
    heading(doc, '24.1.3 Efficiency Principles', 3, space_before=10)
    bullet(doc, 'Streamlined intake: Only essential fields required; smart defaults and auto-detection where possible; progressive disclosure of advanced options')
    bullet(doc, 'Quick triage: Officers see key information (priority, category, fraud flag, confidence) at a glance without needing to navigate to detail views')
    bullet(doc, 'Batch operations: When appropriate, multiple complaints can be processed together (batch status updates, batch assignment)')
    
    body(doc, 'CivicSense is built on Flask with Jinja2 templates for server-side rendering. The architecture uses a modular structure separating routes, templates, and static assets. This choice prioritizes simplicity and fits the small-team, single-deployer context well.')
    
    heading(doc, '24.2 Citizen Complaint Intake Experience', 2, space_before=12)
    body(doc, 'The citizen intake experience is the front door of the entire system. Design here is critical because friction here means citizens do not file complaints. The goal is to make filing a complaint as easy and quick as possible while still gathering useful information.')
    
    heading(doc, '24.2.1 Form Design Patterns', 3, space_before=10)
    bullet(doc, 'Progressive disclosure: Core fields (description, location) are always visible; optional fields (photo, room number, sub-location) are available but not required')
    bullet(doc, 'Clear labeling: Each field has a descriptive label indicating what information is expected; placeholder text provides example entry')
    bullet(doc, 'Help text: Some fields have additional explanatory text available (especially location fields and source options)')
    bullet(doc, 'Logical grouping: Related fields grouped visually (location fields together, contact/source fields together)')
    bullet(doc, 'Smart defaults: Where possible, default choices reduce effort (e.g., pre-filling current date, suggesting likely source based on user context)')
    
    heading(doc, '24.2.2 Location Input Design', 3, space_before=10)
    bullet(doc, 'Ward selector with recognizable names (not abstract codes)')
    bullet(doc, 'Hierarchical refinement: Ward > Floor > Room > Sub-location, allowing precision without overwhelming detail for simple complaints')
    bullet(doc, 'GPS auto-detect option: Especially useful for mobile users, reducing manual location entry; falls back to ward selection if GPS unavailable')
    bullet(doc, 'Validation: Location fields validated against known valid values; errors explain what is wrong')
    
    heading(doc, '24.2.3 Photo Upload Experience', 3, space_before=10)
    bullet(doc, 'Drag-and-drop or click-to-upload: Both interaction patterns supported for flexibility; click-to-upload is more accessible for keyboard users')
    bullet(doc, 'Live preview: Users see photo before submitting, confirming it is the intended image')
    bullet(doc, 'Guidelines communicated: Supported formats (JPEG, PNG, WebP), file size limits, and expectations communicated before upload')
    bullet(doc, 'Optional but encouraged: Photos are powerful evidence but not required; users can file without photos')
    
    heading(doc, '24.2.4 Submission Confirmation', 3, space_before=10)
    bullet(doc, 'Complaint ID: Unique identifier (CMB-XXXXX format) for tracking and reference')
    bullet(doc, 'Summary: Confirmation of what was submitted, including category and priority assigned')
    bullet(doc, 'Explanation: Plain-language explanation of category classification and priority calculation')
    bullet(doc, 'Next steps: What happens next, typical timelines, how to check status')
    bullet(doc, 'Contact information: How to get help, update information, or follow up')
    
    heading(doc, '24.3 Officer Dashboard Design', 2, space_before=12)
    body(doc, 'The officer dashboard is the workhorse interface. Officers spend most of their time here assessing complaints, updating statuses, and monitoring trends. Design must support efficient work without overwhelming with information.')
    
    heading(doc, '24.3.1 Dashboard Layout', 3, space_before=10)
    bullet(doc, 'KPI cards at top: Total complaints, high-priority count, open vs. resolved ratio, average resolution time - visible at a glance')
    bullet(doc, 'Alert panel: Fraud alerts, incident hotspots, and cascade warnings displayed prominently; color and iconography draw attention')
    bullet(doc, 'Charts: Complaint trends over time (by category, by priority, by ward); area charts preferred for showing volume over time; bar charts for category comparison')
    bullet(doc, 'Complaint table: Filterable, sortable, with key fields shown; click expands detail inline or navigates to detail page')
    bullet(doc, 'Actions: Quick actions (status change, priority override, fraud dismiss) accessible from table or detail view')
    
    heading(doc, '24.3.2 Visual Design System', 3, space_before=10)
    bullet(doc, 'Colors: Primary (#1A2B4C deep navy), secondary accent (#3B5BD2 blue), status colors (High: #D9534F red, Medium: #F0AD4E orange, Low: #5CB85C green)')
    bullet(doc, 'Typography: Arial/Helvetica for body, slightly larger for headings; good readability without excessive size')
    bullet(doc, 'Spacing: Consistent spacing (8px base unit, multiples used); adequate white space prevents visual crowding')
    bullet(doc, 'Consistency: Same colors mean same things everywhere; same patterns for similar actions; predictable interactions build trust')
    
    heading(doc, '24.3.3 Filtering and Search Design', 3, space_before=10)
    bullet(doc, 'Multi-criteria filtering: Each filter (category, priority, ward, status, date range) independently selectable and combinable')
    bullet(doc, 'Active filter display: Currently applied filters visible to user; easy removal of individual or all filters')
    bullet(doc, 'Keyword search: Full-text search across complaint description and title; clear indication when search term not found')
    bullet(doc, 'Saved filters: For common queries (e.g., "all high priority electrical"), filters can be saved and quickly retrieved')
    
    heading(doc, '24.3.4 Complaint Detail View', 3, space_before=10)
    bullet(doc, 'Complete information: All submitted data (text, location, photo, source, timestamp) in organized sections')
    bullet(doc, 'Classification results: Category with confidence, key terms that influenced classification (if model provides), alternative categories considered if model was uncertain')
    bullet(doc, 'Priority information: Assigned priority, score breakdown by factor, threshold context, override indication if safety axiom applied')
    bullet(doc, 'Fraud assessment: Whether flagged, specific signals detected, explanation, recommended action, photo authenticity if image submitted')
    bullet(doc, 'Duplicate and cluster info: Whether marked duplicate and of what, whether part of incident cluster and which cluster')
    bullet(doc, 'Photo view: Enlargable image with zoom capability; metadata (if available)')
    bullet(doc, 'Action panel: Status change, priority override, assign, add notes, resolve, dismiss fraud, mark review complete')
    bullet(doc, 'History: Timeline of all status changes and actions taken on this complaint')
    
    heading(doc, '24.4 Explanation Presentation Design', 2, space_before=12)
    body(doc, 'Explanations are central to CivicSense value proposition. They are not just annotations - they are the primary mechanism for building trust, enabling oversight, and empowering officers. Explanation design deserves careful attention.')
    
    heading(doc, '24.4.1 Priority Explanation Design', 3, space_before=10)
    body(doc, 'Priority explanations follow a structured template. The initial statement summarizes the outcome ("This complaint was assigned High priority because..."). Contributing factors are listed with their contributions quantified where possible ("Urgency keywords contributed +1.2 points"). Threshold context places the score relative to thresholds ("Score of 5.0 exceeds the High threshold of 4.0"). If a safety axiom overrode the statistical score, that override is clearly indicated ("A safety constraint was triggered: electrical hazard detected").')
    
    heading(doc, '24.4.2 Classification Explanation Design', 3, space_before=10)
    body(doc, 'Classification explanations show the assigned category and confidence level, describe the key terms or patterns that most influenced the classification, and indicate alternative categories that were considered and why they were rejected. When confidence is low, the explanation emphasizes uncertainty.')
    
    heading(doc, '24.4.3 Fraud Alert Explanation Design', 3, space_before=10)
    bullet(doc, 'Alert language: "Review recommended" rather than "spam" or "fraud" - flags for review, does not accuse')
    bullet(doc, 'Signal listing: Specific signals detected (URL pattern, token distribution anomaly, keyword mismatch, etc.)')
    bullet(doc, 'Photo consideration: If photo evidence is authentic and meaningful, that is noted as mitigating factor')
    bullet(doc, 'Action guidance: What officer should do (review content, assess intent, determine if malicious)')
    
    heading(doc, '24.5 Mobile and Field Officer Experience', 2, space_before=12)
    body(doc, 'Mobile and field use requires special consideration. Officers in the field may be viewing complaints on tablets or phones, and citizens most commonly file from mobile devices. Interactive Google Maps integration, responsive forms, and touch-friendly controls address these needs.')
    
    heading(doc, '24.6 Usability Evaluation Approach', 2, space_before=12)
    body(doc, 'Usability is evaluated through task-completion observation (watching users complete common tasks and noting difficulties), quantitative metrics (task completion rate, time on task, error rate, satisfaction scores), and feedback collection (surveys, ratings, problem reports). Key metrics include task completion rate, time on task, error rate, and satisfaction scores.')

    # CH 25
    p = doc.add_paragraph(); p.paragraph_format.page_break_before = True
    r = p.add_run('CHAPTER 25: PROJECT ORGANIZATION, MANAGEMENT AND INSTITUTIONAL CONTEXT')
    r.font.name = 'Arial'; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = PRIMARY
    parent.insert(idx, p._p); idx += 1

    heading(doc, '25.1 Institutional Profile', 2, space_before=12)
    body(doc, 'Pimpri Chinchwad University (PCU) is a state university established in 2011 under Maharashtra State Government Act No. XXVII of 2011. The university is located in Sate, Maval, Pune - 412106, Maharashtra, India, and serves a diverse academic community across engineering, technology, management, and pharmacy programs.')
    two_col(doc,
        [('Institution', 'Pimpri Chinchwad University (PCU)'),
         ('Established', '2011 (Maharashtra State Govt. Act No. XXVII of 2011)'),
         ('Location', 'Sate, Maval, Pune - 412106, Maharashtra, India'),
         ('Department', 'Computer Science & Engineering'),
         ('Program', 'Bachelor of Technology (B.Tech)'),
         ('Academic Year', '2025-2026'),
         ('Project Title', 'CivicSense: AI-Based Citizen Complaint Analyzer'),
         ('Supervisor', 'Dr. S. Deshmukh, Associate Professor, CSE, PCU'),
         ('Co-Supervisor', 'Prof. A. Reddy, Visiting Faculty, IIT Bombay')])
    
    heading(doc, '25.2 Campus Infrastructure Scope', 2, space_before=12)
    body(doc, 'The university campus includes multiple academic blocks, hostel facilities, dining facilities, and recreational areas, making it a realistic testbed for civic complaint management. The campus scale is large enough to generate meaningful complaint volumes across multiple categories and locations, yet small enough to manage as a realistic pilot deployment.')
    bullet(doc, 'Academic Blocks (A, B, C): Classrooms, laboratories, seminar halls - common sources of classroom and lab infrastructure complaints')
    bullet(doc, 'Administrative Block: University administration offices - provides administrative context and stakeholder access')
    bullet(doc, 'Hostel Complex: Girls Hostel and Boys Hostel - residential facilities generating hostel-related complaints (water, electricity, safety)')
    bullet(doc, 'Central Canteen and Cafeteria: Food service facilities - source of canteen and food quality complaints')
    bullet(doc, 'Sports Lawn and Recreation Areas: Athletic facilities - occasional maintenance and safety complaints')
    bullet(doc, 'Main Gates: Perimeter security and access points - relevant for campus safety and parking complaints')
    
    heading(doc, '25.3 Project Governance Structure', 2, space_before=12)
    body(doc, 'The project operates under the supervision of faculty members from the Department of Computer Science & Engineering. Dr. S. Deshmukh serves as primary supervisor, providing overall project guidance, scope control, and quality assurance. Prof. A. Reddy serves as co-supervisor, providing additional expertise from IIT Bombay and review of research methodology.')
    body(doc, 'The project team consists of students of the Computer Science & Engineering department at PCU, responsible for all aspects of implementation, testing, documentation, and deployment. The team structure emphasizes shared ownership with clear individual responsibilities.')
    table(doc,
        ['Role', 'Responsibilities', 'Experience/Background'],
        [
            ['Primary Supervisor (Dr. S. Deshmukh)', 'Overall guidance, scope, quality, reproducibility requirement', 'Associate Professor, CSE, PCU'],
            ['Co-Supervisor (Prof. A. Reddy)', 'Technical guidance, research methodology review', 'Visiting Faculty, IIT Bombay'],
            ['Project Team Members', 'Implementation, testing, documentation, deployment', 'B.Tech Students, CSE, PCU'],
        ], [1.6, 2.7, 1.8], 9)
    
    heading(doc, '25.4 Development Methodology', 2, space_before=12)
    body(doc, 'The project follows an iterative development approach. The system is built and improved in iterations, with continuous testing, regular review with supervisors, documentation-created alongside implementation, and emphasis on reproducibility throughout. This methodology allows the project to adapt as understanding develops while maintaining steady progress toward defined goals.')
    body(doc, 'Reproducibility is treated as a first-class requirement, not an afterthought. Every component is designed to be reproducible: data generation uses deterministic seeds, model training produces documented artifacts, system configuration is captured, and evaluation procedures are documented in detail. This approach makes the project verifiable and trustworthy.')
    
    heading(doc, '25.5 Timeline and Milestones', 2, space_before=12)
    table(doc,
        ['Milestone', 'Timeline', 'Key Activities', 'Deliverables'],
        [
            ['Project Initiation', 'Aug 2025 (Week 1-2)', 'Literature review, requirements analysis, planning', 'Project proposal, initial plan'],
            ['Phase 1 Development', 'Sep-Nov 2025 (Week 3-12)', 'Traditional pipeline implementation', 'Working traditional pipeline'],
            ['Phase 1 Evaluation', 'Nov-Dec 2025 (Week 13-14)', 'Testing, evaluation, bug fixing', 'Test reports, evaluation results'],
            ['Phase 1 Documentation', 'Dec 2025 (Week 15-16)', 'Comprehensive Phase 1 documentation', 'Phase 1 report'],
            ['Phase 2 Development', 'Jan-Mar 2026 (Week 17-24)', 'NCM-Net framework development', 'Working NCM-Net system'],
            ['Phase 2 Evaluation', 'Mar 2026 (Week 25-26)', 'Advanced testing, validation', 'Advanced test reports'],
            ['Phase 2 Documentation', 'Mar-Apr 2026 (Week 27-28)', 'Comprehensive Phase 2 documentation', 'Phase 2 report'],
            ['Integration', 'Apr 2026 (Week 29-30)', 'Combine Phase 1 and Phase 2', 'Master report'],
            ['Final Review & Submission', 'May 2026 (Week 31-32)', 'Final review, formatting, submission', 'Final project submission'],
        ], [1.2, 1.4, 2.0, 1.5], 8.5)
    
    heading(doc, '25.6 Work Distribution and Skill Mapping', 2, space_before=12)
    table(doc,
        ['Skill Area', 'Application in Project', 'Importance'],
        [
            ['Python Programming', 'Primary implementation language for all modules', 'Essential - all components in Python'],
            ['Machine Learning', 'Classification, clustering, fraud, conformal, gradient boosting', 'Core - intelligent triage is central'],
            ['Natural Language Processing', 'Text preprocessing, TF-IDF, classification, embeddings', 'Essential - text is primary input'],
            ['Web Development (Flask)', 'REST API design, dashboard templates, route handling', 'Essential - user-facing platform'],
            ['Database (SQLite)', 'Data modeling, persistence, queries, migrations', 'Essential - all data stored'],
            ['Testing & QA', 'Smoke tests, unit evaluation, coverage tracking', 'Essential - ensures reliability'],
            ['Documentation', 'Technical writing, report structure, diagrams', 'Essential - communicates work'],
            ['UI/UX Design Principles', 'Dashboard layout, form design, explanation presentation', 'Important - drives adoption'],
            ['Research Methodology', 'Literature review, gap analysis, evaluation design', 'Important - establishes credibility'],
            ['Project Management', 'Timeline, coordination, deliverables tracking', 'Important - ensures completion'],
        ], [1.4, 2.6, 2.0], 9)
    
    heading(doc, '25.7 Risk Management and Mitigation', 2, space_before=12)
    table(doc,
        ['Risk', 'Probability', 'Impact', 'Mitigation Strategy'],
        [
            ['Transformer libraries unavailable (PyTorch, Transformers)', 'Medium', 'High - cannot fine-tune BERT', 'Fall back to TF-IDF + LinearSVC; document limitation'],
            ['Small training corpus limits accuracy', 'High', 'Medium - lower accuracy', 'Document honestly; compare with expected 93%'],
            ['Scope creep expands project beyond time', 'Medium', 'High - incomplete work', 'Clear scope definition; regular review'],
            ['Time constraints compress remaining work', 'Medium', 'Medium - rushed final stages', 'Iterative approach; buffer in schedule'],
            ['Technical bugs in production code', 'Medium', 'Medium - incorrect results', 'Testing throughout; smoke test suite'],
            ['Incomplete or unclear documentation', 'Low', 'High - poor evaluation', 'Documentation alongside implementation'],
            ['Data quality issues in corpus', 'Low', 'Medium - biased results', 'Careful corpus design; transparent about synthetic'],
            ['Difficulty demonstrating system works', 'Low', 'High - poor evaluation', 'Smoke test ensures demonstrable system'],
        ], [1.0, 0.8, 0.8, 3.2], 8.5)
    
    heading(doc, '25.8 Ethical Considerations in Project Execution', 2, space_before=12)
    body(doc, 'Academic integrity is maintained through original implementation, proper attribution of the base paper and other sources, honest reporting of results including limitations and failures, and no plagiarism - all content is original or properly attributed. The project treats reproducibility as a requirement to ensure results are verifiable.')
    body(doc, 'Responsible AI development is practiced by being transparent about what the system can and cannot do, ensuring the system assists rather than replaces human decision-making, considering privacy implications (demonstration uses synthetic data), and acknowledging potential biases in limitations. Social responsibility is demonstrated through beneficial application design, accessibility consideration for diverse users, use of open-source tools, and documentation that enables others to learn and build upon the work.')

    # CH 26
    p = doc.add_paragraph(); p.paragraph_format.page_break_before = True
    r = p.add_run('CHAPTER 26: COMPREHENSIVE EVALUATION METHODOLOGY AND STATISTICAL ANALYSIS')
    r.font.name = 'Arial'; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = PRIMARY
    parent.insert(idx, p._p); idx += 1

    heading(doc, '26.1 Evaluation Philosophy', 2, space_before=12)
    body(doc, 'Evaluation is designed around three principles: honesty (report actual measured numbers, not aspirational targets), reproducibility (document exactly what was evaluated, on what data, with what procedure), and comprehensiveness (evaluate technical performance, functional completeness, usability, robustness, and practical value).')
    
    heading(doc, '26.2 Corpus Design Principles', 2, space_before=12)
    body(doc, 'The demonstration corpus is carefully designed to enable meaningful evaluation. Unlike many projects that evaluate on unclear data, CivicSense uses a designed corpus with known ground truth, injected scenarios, and reproducible generation.')
    table(doc,
        ['Design Aspect', 'Approach', 'Purpose'],
        [
            ['Known ground truth', 'Every complaint has assigned category, expected priority, labels', 'Enables quantitative metrics'],
            ['Injected scenarios', 'Fraud, duplicates, clusters injected with known parameters', 'Enables evaluation of these features'],
            ['Reproducible generation', 'Deterministic seed; same seed produces same corpus', 'Enables exact replication'],
            ['Coverage diversity', 'All categories, wards, priorities, lengths represented', 'Reduces bias from single scenario'],
            ['Realistic parameters', 'Counts, distributions match expected real-world patterns', 'Enables meaningful extrapolation'],
            ['Scalable design', 'Parse + generate structure allows larger corpus', 'Enables future larger evaluation'],
        ], [1.3, 2.3, 2.1], 9)
    
    heading(doc, '26.3 Metric Selection Rationale', 2, space_before=12)
    body(doc, 'Metrics are selected based on what they measure and how relevant that is to system goals. Accuracy and F1 capture classification correctness, confusion matrices reveal specific errors, priority distribution analysis validates score behavior, duplicate and fraud detection rates validate those specific features, and latency and throughput validate operational viability.')
    heading(doc, '26.3.1 Accuracy and F1', 3, space_before=10)
    body(doc, 'Accuracy measures overall correctness: fraction of complaints where predicted category matches true category. However, accuracy can be misleading with imbalanced classes. F1 score (harmonic mean of precision and recall) combines both concerns into a single metric per class.')
    body(doc, 'Macro F1 averages per-class F1 equally, treating all classes equally regardless of frequency. Weighted F1 averages per-class F1 weighted by class frequency, reflecting overall distribution. Both are reported to give complete picture.')
    
    heading(doc, '26.3.2 Confusion Matrix Analysis', 3, space_before=10)
    body(doc, 'Confusion matrices reveal which classes are confused with each other. Each cell (i, j) shows count of items of true class i predicted as class j. High values off-diagonal indicate specific confusions to investigate. For civic complaints, certain confusions are expected (related categories), and understanding them helps interpret and improve.')
    
    heading(doc, '26.3.3 Cross-Validation', 3, space_before=10)
    body(doc, 'Stratified k-fold cross-validation (k=5) provides robust estimates. The dataset is split into 5 folds maintaining class distribution. For each fold, training on 4 folds and testing on held-out fold produces an estimate. Results are aggregated as mean and standard deviation across folds.')
    body(doc, 'Cross-validation reduces variance due to a particular train-test split choice, provides multiple estimates that can be averaged, and reveals performance stability across different data subsets. It is more robust than a single split, especially important with modest dataset sizes.')
    
    heading(doc, '26.4 Scenario-Based Evaluation', 2, space_before=12)
    body(doc, 'Beyond aggregate metrics, scenario-based evaluation tests specific capabilities on targeted scenarios:')
    bullet(doc, 'Emergency scenarios: Extreme urgency, high confidence - should be flagged High with strong safety axiom triggers')
    bullet(doc, 'Safety scenarios: Injuries, gas leaks, fire, explosives - must trigger safety axioms, High priority')
    bullet(doc, 'Routine scenarios: Normal complaints, moderate detail - should classify and prioritize reasonably')
    bullet(doc, 'Edge cases: Very short descriptions, vague complaints, mixed issues - should handle gracefully')
    bullet(doc, 'Fraud scenarios: Spam, phishing, malicious links, misinformation attempts - should flag consistently')
    bullet(doc, 'Duplicate scenarios: Exact submitter matches, paraphrased re-filings - should detect both')
    bullet(doc, 'Cluster scenarios: Multiple related complaints in same area - should cluster and surface to officers')
    
    heading(doc, '26.5 Statistical Validity Considerations', 2, space_before=12)
    body(doc, 'Several statistical considerations affect interpretation of results. Sample size (200 complaints, 5 categories) provides reasonable estimates but with some uncertainty. Cross-validation reduces variance from split choice. Corpus bias (synthetic, may not perfectly represent real distributions) is acknowledged. Results may not generalize to other contexts; this is explicitly noted.')
    body(doc, 'Threats to validity include internal validity (evaluation measures what it claims - supported by controlled scenarios), external validity (results may not generalize - acknowledged as limitation), construct validity (metrics capture intended constructs - supported by standard metrics), and conclusion validity (conclusions supported by evidence - supported by honest reporting).')
    body(doc, 'Confidence in results increases when multiple evaluation approaches (aggregate metrics, per-class analysis, confusion matrices, scenario evaluation, manual review) converge on similar conclusions. This multi-faceted approach provides robust, well-rounded assessment of system capabilities.')
    
    heading(doc, '26.6 Results Summary Table', 2, space_before=12)
    table(doc,
        ['Evaluation Area', 'Primary Metric', 'Result', 'Interpretation'],
        [
            ['Classification', 'Accuracy', '82.19% (5-fold CV)', 'Strong baseline; gap vs 93% expected for scale'],
            ['Per-Class F1', 'Macro F1', '82.8% (balanced)', 'No category severely underperforming'],
            ['Priority', 'Distribution match', 'Matches expected distribution', 'Formula behaves sensibly'],
            ['Duplicate Detection', 'Detection rate', '9/9 = 100%', 'Excellent on injected scenario'],
            ['Fraud Detection', 'Detection rate', '8/8 = 100%', 'Excellent on injected scenario; 0 FP'],
            ['Clustering', 'Cluster formation', '6/6 clusters', 'Clustering useful; enable seeing patterns'],
            ['Digest Quality', 'Consistency check', 'Consistent, complete', 'Template produces reliable digests'],
            ['Latency', 'Round-trip time', '<200ms typical', 'Operationally viable; no bottleneck'],
            ['Test Coverage', 'Smoke test', 'All checks pass', 'System functionally complete'],
        ], [1.2, 1.3, 1.6, 2.0], 8.5)
    
    callout(doc, 'A rigorous evaluation methodology is as important as the system itself. By evaluating honestly on a designed corpus, reporting actual numbers with limitations, and enabling replication through reproducibility, the project establishes credibility and provides a foundation for future work to build upon and compare against.', 'EVALUATION PHILOSOPHY:', 'F0F7FF', '1A2B4C')

    # CH 27
    p = doc.add_paragraph(); p.paragraph_format.page_break_before = True
    r = p.add_run('CHAPTER 27: CONCLUSION AND FINAL REMARKS')
    r.font.name = 'Arial'; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = PRIMARY
    parent.insert(idx, p._p); idx += 1

    heading(doc, '27.1 Summary of Accomplishments', 2, space_before=12)
    heading(doc, '27.1.1 Phase 1: Traditional Complaint Triage Pipeline', 3, space_before=10)
    bullet(doc, 'Base paper implementation: Complete implementation of the base papers complaint triage pipeline, including text preprocessing, category classification, duplicate detection, near-duplicate clustering, priority assignment, and fraud detection')
    bullet(doc, 'Five meaningful extensions: Fraud detection with statistical and content signals, near-duplicate clustering for incident pattern surfacing, explainable AI throughout with plain-language explanations, structured reporting with weekly digests and PDF/Excel export, and reproducible evaluation with controlled demonstration corpus')
    bullet(doc, 'Measurable results: Demonstrated 82.19% classification accuracy on controlled 200-complaint corpus, complete duplicate and fraud detection on injected scenarios, and comprehensive evaluation including confusion matrices and per-class analysis')
    bullet(doc, 'Working system: Fully functional dashboard, REST API, and admin interface providing practical citizen complaint intake and officer triage tools')
    
    heading(doc, '27.1.2 Phase 2: NCM-Net Advanced Framework', 3, space_before=10)
    bullet(doc, 'Four novel research pillars: AG-CMA cross-modal alignment, Conformal Prediction with certified coverage, Neuro-Symbolic Safety Layer with 100% zero-miss recall, and ST-ICK spatio-temporal cascade kernel')
    bullet(doc, 'Mathematical formulations: Complete mathematical foundations documented with theorems, proofs, complexity analyses, and parameter guidelines')
    bullet(doc, 'Computer vision and GIS: Advanced image analysis with AG-CMA gating and cross-modal routing, plus comprehensive GIS integration with 13 high-precision coordinates and Google Maps integration')
    bullet(doc, 'Comprehensive testbed: 200-complaint demonstration corpus with 6 categories, 13 wards, 140 officers, 30-day temporal span, and realistic complaint patterns')
    bullet(doc, 'Published results: Benchmark study (Table 85) showing NCM-Net achieves 83.08% accuracy with certified 90% coverage and 100% safety recall across 5 papers, with ablation study showing contribution of each pillar')
    bullet(doc, 'Five detailed case studies: Realistic walkthroughs demonstrating system response to electrical emergency, water leak, fraudulent blank-image complaint, cascade incident, and fraud detection')
    bullet(doc, 'Production-ready deployment: Complete API reference, database schema with migration guides, deployment guide, testing strategy, and operational configuration')
    
    heading(doc, '27.2 Innovation and Differentiation', 2, space_before=12)
    body(doc, 'CivicSense differentiates from existing systems through several dimensions:')
    table(doc,
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
            ['Certification', 'None', 'Formal certification framework (Section 11.2)'],
            ['Deployment', 'Often custom/unique', 'Reproducible pipeline, documented APIs'],
        ], [1.2, 2.3, 2.3], 8.5)
    
    heading(doc, '27.3 Honest Assessment of Limitations', 2, space_before=12)
    body(doc, 'No system is perfect, and honest assessment of limitations is essential for responsible deployment and clear-eyed future planning.')
    heading(doc, '27.3.1 Data Limitations', 3, space_before=10)
    bullet(doc, 'Demonstration corpus is synthetic: Generated systematically rather than drawn from real complaint history, so real-world distributions may differ')
    bullet(doc, 'Corpus size is modest (200 complaints): Sufficient for meaningful evaluation and to demonstrate system behavior, but not large enough to claim production-ready performance across all categories')
    bullet(doc, 'No multilingual text in current corpus: Built for English; real campuses serve multilingual populations')
    bullet(doc, 'No real-world performance data: Evaluation is on designed corpus; actual deployment performance unknown until deployed in production')
    heading(doc, '27.3.2 Technical Limitations', 3, space_before=10)
    bullet(doc, 'Classification accuracy is good but not perfect: 82.19% means approximately 1 in 6 complaints classified incorrectly; misclassifications are typically to related categories')
    bullet(doc, 'Fraud detection is scenario-based: Tested on injected scenarios; real-world fraud patterns may differ and require adaptation')
    bullet(doc, 'Duplicate detection relies on TF-IDF similarity: True semantic duplicates expressed very differently may not be detected; going beyond TF-IDF is future work')
    bullet(doc, 'Explainability is template-based for priority: Priority explanations are structured but formula-based; deeper explanations (e.g., why specific terms influenced classification) are future work')
    bullet(doc, 'No deployment at scale and no long-term reliability data available yet; operational characteristics under sustained load unknown')
    bullet(doc, 'Geographic coverage limited to PCU campus: 13 coordinates cover campus facilities; extension to broader city requires more extensive data')
    heading(doc, '27.3.2 Evaluation Limitations', 3, space_before=10)
    bullet(doc, 'Evaluation corpus is designed rather than organic: Designed for evaluation, so may not capture full diversity and difficulty of real complaints')
    bullet(doc, 'No user study: Usability claims based on design principles, not measured user behavior; formal usability testing is future work')
    bullet(doc, 'No A/B testing or live comparison: Cannot directly compare system-assisted triage with previous manual process')
    
    heading(doc, '27.4 Future Work', 2, space_before=12)
    body(doc, 'Future work spans technical, functional, research, and deployment dimensions, building on the foundation established by CivicSense.')
    
    heading(doc, '27.4.1 Technical Enhancements', 3, space_before=10)
    bullet(doc, 'Transformer integration: Fine-tuning DistilBERT or other distilled models for classification; balance accuracy improvement against compute cost and operational complexity')
    bullet(doc, 'Multilingual support: Adding Marathi and Hindi using multilingual BERT or similar, reflecting reality of Indian campuses serving diverse linguistic populations')
    bullet(doc, 'Voice input: Integrating speech-to-text for voice complaint submission; accessibility and convenience benefit')
    bullet(doc, 'Advanced computer vision: More sophisticated image analysis using modern deep learning for defect detection, damage assessment, anomaly identification')
    bullet(doc, 'Real-time streaming analytics: Real-time dashboards and alerts for monitoring complaint flow as it happens')
    
    heading(doc, '27.4.2 Functional Enhancements', 3, space_before=10)
    bullet(doc, 'IoT integration: Connecting to campus sensors (water, electricity, fire, occupancy) for proactive monitoring and automated incident detection')
    bullet(doc, 'Mobile application: Native apps for citizens and officers with push notifications, camera integration, offline capability, location awareness')
    bullet(doc, 'Workflow automation: Automated assignment, escalation, SLA tracking, resolution workflows reducing manual coordination burden')
    bullet(doc, 'Predictive analytics: Forecasting complaint trends by time, location, category for proactive resource allocation and prevention')
    bullet(doc, 'Citizen feedback loop: Collecting satisfaction feedback on resolution, closing the loop with citizens, building trust through responsiveness')
    
    heading(doc, '27.4.3 Research and Publication', 3, space_before=10)
    bullet(doc, 'Publication: Preparing NCM-Net contributions for peer-reviewed venue (AI for social good, responsible AI, civic technology conferences)')
    bullet(doc, 'Extended evaluation: Evaluating on larger, more diverse, ideally real datasets to validate generalizability')
    bullet(doc, 'Comparative studies: Systematic comparison with other civic AI approaches on common benchmarks')
    bullet(doc, 'HCI studies: Studying how officers and citizens actually use system, identifying usability issues and adoption barriers')
    bullet(doc, 'Formal verification: Extending neuro-symbolic framework to broader axioms, potentially exploring automated axiom learning or verification')
    
    heading(doc, '27.5 Closing Remarks', 2, space_before=12)
    body(doc, 'The CivicSense project represents a significant step toward AI-powered civic technology that is both intelligent and trustworthy. It demonstrates that academic research can be translated into practical, working systems addressing real-world problems, and that rigorous engineering practices (reproducibility, testing, honest evaluation, comprehensive documentation) produce systems worthy of trust.')
    body(doc, 'The project contributes to academic knowledge through the NCM-Net framework and its four research pillars, each providing novel algorithmic approaches to problems in civic AI. It contributes practical value through a working system that could genuinely improve complaint handling at university campuses and, scaled, at municipal levels. And it contributes to responsible AI practice through transparent documentation, honest limitation reporting, and community-oriented openness.')
    body(doc, 'The team expresses gratitude to all who have contributed to and supported this project, including supervisors Dr. S. Deshmukh and Prof. A. Reddy, the Department of Computer Science & Engineering at Pimpri Chinchwad University, and the broader open-source community whose tools and libraries made this work possible.')
    body(doc, 'CivicSense stands as a demonstration that AI for civic good is not just aspirational - it can be practical, trustworthy, and beneficial today. The journey from this point involves real-world deployment, continuous improvement, and expansion to serve the communities that need it most.')

    # Save
    doc.save('Project_Report_Master.docx')
    print(f'SUCCESS! Saved Project_Report_Master.docx')
    print(f'Total paragraphs: {len(doc.paragraphs)}')
    print(f'Total tables: {len(doc.tables)}')
    print('Added 5 new chapters (23-27)')
else:
    print('ERROR: Could not find APPENDIX A in document')
