# Customer Support Email Agent

<div align="center">

<p align="center">
  <a href="../README.md">⬅️ Kembali ke Repositori Utama</a> •
  <a href="email_agent_architecture.svg">📊 Lihat Diagram SVG Arsitektur</a>
</p>

</div>

---

Agentic system design untuk mengotomatisasi pemrosesan email customer support dengan tetap menjaga kontrol manusia pada kasus berisiko tinggi dan membatasi jawaban berdasarkan internal knowledge base.

## Tujuan

Sistem dirancang untuk:

- Mengklasifikasikan email customer support ke beberapa kategori seperti Billing, Technical, dan Feedback.
- Mengambil informasi dari internal knowledge base berupa PDF atau FAQ.
- Membuat draft respons berdasarkan sumber internal.
- Mendeteksi kasus kritis sebelum membuat draft.
- Mengarahkan kasus kritis ke human agent.
- Mencegah model mengarang informasi, khususnya terkait refund policy.

Requirement ini mengikuti brief Part 1 pada assessment.

## Arsitektur

```text
                         CUSTOMER EMAIL
                               |
                               v
                    +----------------------+
                    | Email Ingestion      |
                    +----------------------+
                               |
                               v
                    +----------------------+
                    | Critical Issue Check |
                    +----------------------+
                         /            \
                       YES             NO
                        |               |
                        v               v
                 HUMAN AGENT       CLASSIFIER
                                       |
                            +----------+----------+
                            |          |          |
                            v          v          v
                         Billing   Technical   Feedback
                            |          |          |
                            +----------+----------+
                                       |
                                       v
                           INTERNAL KNOWLEDGE BASE
                              PDF / FAQ / Policy
                                       |
                                       v
                              RESPONSE DRAFTING
                                       |
                                       v
                              POLICY VALIDATION
                                       |
                                       v
                              HUMAN REVIEW / SEND
```

## Critical Issue Detection

Critical issues harus diperiksa **sebelum drafting**, sesuai requirement assessment.

Email langsung diarahkan ke human agent apabila:

1. Email menyebut:
   - Data loss
   - Service outage
   - Security breach
2. Customer telah menghubungi support **lebih dari 3 kali dalam 7 hari**.

Kondisi tersebut tidak menunggu proses drafting. Sistem melakukan pengecekan terlebih dahulu agar kasus berisiko tidak mendapatkan respons otomatis yang tidak sesuai.

Contoh:

```text
Email
  |
  v
Critical Check
  |
  +-- "security breach" --> HUMAN
  |
  +-- "data loss" -------> HUMAN
  |
  +-- "service outage" --> HUMAN
  |
  +-- >3 contacts/7d ---> HUMAN
  |
  +-- tidak ada ---------> lanjut
```

## Email Classification

Email dikategorikan berdasarkan intent.

Contoh kategori:

```text
Billing
Technical
Feedback
```

Classifier dapat dikembangkan dengan kategori tambahan tanpa mengubah keseluruhan workflow.

Output classifier sebaiknya memiliki struktur terkontrol, misalnya:

```json
{
  "category": "Technical",
  "confidence": 0.94
}
```

Confidence dapat digunakan sebagai tambahan safety check. Jika confidence terlalu rendah, email dapat diarahkan ke human review daripada memaksakan klasifikasi.

## Internal Knowledge Base

Respons tidak dibuat berdasarkan pengetahuan umum model.

Sumber respons berasal dari internal knowledge base:

```text
PDF / FAQ / Policy
       |
       v
Document ingestion
       |
       v
Text extraction
       |
       v
Chunking
       |
       v
Retrieval
       |
       v
Relevant knowledge
       |
       v
Response drafting
```

Untuk pertanyaan mengenai refund, sistem hanya boleh menggunakan informasi yang ditemukan pada refund policy internal.

Jika informasi refund tidak ditemukan, sistem tidak boleh membuat atau menebak policy.

Contoh perilaku aman:

```text
Customer:
"Apakah saya bisa mendapatkan refund setelah 45 hari?"

Knowledge Base:
Tidak ada informasi mengenai refund setelah 45 hari.

Agent:
"Terdapat informasi yang belum dapat saya verifikasi
dari knowledge base kami. Saya akan meneruskan pertanyaan
ini kepada tim support."
```

Bukan:

```text
"Ya, refund tersedia sampai 60 hari."
```

jika angka tersebut tidak terdapat pada knowledge base.

## Drafting Response

Setelah email lolos critical check dan diklasifikasikan:

```text
Email
  |
  v
Category
  |
  v
Retrieve relevant knowledge
  |
  v
Generate draft
  |
  v
Validate against source
  |
  v
Human review / send
```

Prompt drafting harus membatasi model agar:

- hanya menggunakan informasi dari retrieved internal knowledge;
- tidak mengarang policy;
- tidak membuat refund terms baru;
- tidak menggunakan pengetahuan eksternal untuk menjawab policy;
- meminta human review jika informasi yang diperlukan tidak tersedia.

## Failure Points & Mitigations

| Failure Point | Mitigation |
|---|---|
| Critical issue terlewat | Critical check dilakukan sebelum drafting |
| Customer terlalu sering menghubungi support | Hitung riwayat kontak dalam rolling 7 hari |
| Salah klasifikasi | Confidence threshold + human review |
| Knowledge base tidak memiliki jawaban | Jangan mengarang; escalate |
| Refund policy hallucination | Source-grounded response + policy validation |
| PDF sulit diproses | Validasi extraction dan document parsing |
| Knowledge retrieval salah | Gunakan relevance threshold dan fallback |
| LLM menghasilkan respons tidak sesuai | Output validation sebelum dikirim |
| Service/API error | Retry, timeout, dan fallback ke human |
| Beban tinggi | Queue-based processing dan asynchronous workers |

## Operational Thinking

Sistem sebaiknya memiliki observability untuk membantu mengetahui apakah agent bekerja dengan benar.

Data yang dapat dicatat:

```text
email_id
timestamp
category
critical_flag
escalation_reason
retrieval_success
draft_status
human_review
processing_latency
error_type
```

Hindari logging informasi sensitif customer secara berlebihan.

Metric yang dapat dipantau:

- classification accuracy;
- escalation rate;
- retrieval success rate;
- draft acceptance rate;
- hallucination/policy violation rate;
- processing latency;
- API failure rate.

## Reliability

Reliability dibangun melalui beberapa lapisan:

```text
Input Validation
       |
       v
Critical Routing
       |
       v
Classification
       |
       v
Knowledge Retrieval
       |
       v
Grounded Draft
       |
       v
Output Validation
       |
       v
Human Review
```

Jika salah satu komponen penting gagal, sistem sebaiknya **fail safely** dengan mengarahkan email ke human agent daripada menghasilkan jawaban yang tidak dapat diverifikasi.

## Trade-offs

### Automation vs Human Oversight

Otomatisasi mempercepat pemrosesan email, tetapi kasus kritis tetap diarahkan ke manusia.

Trade-off:

- lebih aman;
- tetapi membutuhkan human workload lebih tinggi.

### Strict Knowledge Grounding vs Answer Coverage

Membatasi jawaban pada knowledge base mengurangi hallucination, tetapi agent mungkin tidak dapat menjawab pertanyaan yang belum terdokumentasi.

Dalam kondisi tersebut, sistem memilih escalation daripada mengarang jawaban.

### Confidence Threshold

Confidence threshold membantu menangani klasifikasi yang ambigu, tetapi terlalu tinggi dapat meningkatkan jumlah email yang masuk human review.

Threshold perlu dievaluasi menggunakan data historis.

## Agentic Decision Flow

Sistem tidak sekadar menjalankan pipeline statis.

Agent membuat keputusan berdasarkan kondisi email:

```text
Receive Email
     |
     v
"Is this critical?"
     |
   YES ---> Human
     |
     NO
     |
     v
"What category is this?"
     |
     v
"Do I have relevant internal knowledge?"
     |
   NO ---> Human / clarification
     |
     YES
     |
     v
"Can I safely draft a grounded response?"
     |
   NO ---> Human
     |
     YES
     |
     v
Draft Response
```

Dengan demikian, agent memiliki beberapa titik pengambilan keputusan dan tidak hanya menjalankan satu prompt untuk semua email.

## Security & Privacy

- API keys disimpan melalui environment variables.
- Credential tidak disimpan di source code.
- Internal PDF/FAQ tidak dikirim ke pihak yang tidak diperlukan.
- Log meminimalkan data customer yang sensitif.
- Akses knowledge base menggunakan permission yang sesuai.
- Draft kritis tidak dikirim otomatis tanpa human review.

## Catatan Implementasi Teknis (Blueprint Produksi)

Part 1 merupakan spesifikasi desain arsitektur (*System Design & Critical Thinking*) yang disajikan melalui dokumen analisis ini dan diagram visual [email_agent_architecture.svg](email_agent_architecture.svg). 

Jika sistem ini dikembangkan lebih lanjut ke tahap implementasi kode produksi (*production deployment*), berikut adalah spesifikasi environment dan struktur modular yang direkomendasikan:

```env
GEMINI_API_KEY=your_api_key
```

### Rekomendasi Struktur Direktori Produksi:

```text
.
├── README.md
├── src/
│   ├── classifier.py
│   ├── router.py
│   ├── knowledge_base.py
│   ├── drafter.py
│   ├── validators.py
│   └── main.py
├── knowledge/
│   ├── faq.pdf
│   └── refund_policy.pdf
├── tests/
│   ├── test_classifier.py
│   ├── test_router.py
│   └── test_policy_guardrail.py
├── requirements.txt
├── .env
└── .gitignore
```

## Assessment Mapping

| Assessment Requirement | Implementation |
|---|---|
| Multiple email categories | Intent classifier |
| Internal PDFs/FAQs | Knowledge base + retrieval |
| Critical technical routing | Critical issue check |
| Data loss detection | Pre-drafting escalation |
| Service outage detection | Pre-drafting escalation |
| Security breach detection | Pre-drafting escalation |
| >3 contacts in 7 days | Contact-history check |
| Prevent refund hallucination | Grounded policy retrieval + validation |
| Reliability | Retry, timeout, fallback |
| Operational thinking | Logging, metrics, testing, observability |

Requirement mapping di atas berdasarkan brief Part 1 dan success criteria assessment.

## Success Criteria

Assessment mengevaluasi:

- **System Reliability** — kemampuan menangani error dan mempertahankan performa.
- **Code Quality** — modularity, documentation, dan clean code.
- **Agentic Logic** — penggunaan planning/reasoning pattern, bukan sekadar script execution.
- **Operational Thinking** — logging, testing, dan observability/AgentOps.

README ini menjelaskan desain yang dapat digunakan sebagai dasar implementasi dan presentasi arsitektur saat interview.
