"""
SQLAlchemy database models for production-ready RAG service.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """Document metadata model."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    status = Column(String(50), default="processing")  # processing, completed, failed
    chunks_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Document chunk with embedding stored in PostgreSQL."""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Full chunk content
    content_preview = Column(Text)  # First 200 chars for preview
    embedding = Column(Vector(1536))  # pgvector: 1536 dimensions for OpenAI embeddings
    chunk_metadata = Column(Text)  # JSON metadata as text (renamed from 'metadata' to avoid SQLAlchemy conflict)
    source_type = Column(String(50), default="document", index=True)  # document, sec_filing
    form_type = Column(String(20), index=True)
    cik = Column(String(10), index=True)
    accession_number = Column(String(25), index=True)
    filed_date = Column(Date, index=True)
    filing_section = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class Query(Base):
    """Query history and analytics."""
    __tablename__ = "queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sources_count = Column(Integer, default=0)
    latency_ms = Column(Float)
    model = Column(String(100))
    provider = Column(String(50))
    tokens_used = Column(Integer)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="queries")


class APIKey(Base):
    """API key management."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    rate_limit = Column(Integer, default=100)  # requests per hour
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class SECCompany(Base):
    """SEC company metadata."""
    __tablename__ = "sec_companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cik = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255))
    ticker = Column(String(20))
    sic_code = Column(String(10))
    state_of_incorporation = Column(String(50))
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    filings = relationship("SECFiling", back_populates="company", cascade="all, delete-orphan")


class SECFiling(Base):
    """SEC filing metadata."""
    __tablename__ = "sec_filings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    accession_number = Column(String(25), unique=True, nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("sec_companies.id"), nullable=False, index=True)
    form_type = Column(String(20), nullable=False, index=True)
    filed_date = Column(Date, nullable=False, index=True)
    accepted_date = Column(DateTime)
    filing_url = Column(Text, nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, index=True)
    status = Column(String(20), default="discovered")  # discovered, downloading, indexing, indexed, failed
    filing_metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("SECCompany", back_populates="filings")
    document = relationship("Document")


class FilingCrossReference(Base):
    """Cross-references between filings."""
    __tablename__ = "filing_cross_references"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_filing_id = Column(UUID(as_uuid=True), ForeignKey("sec_filings.id"), nullable=False, index=True)
    target_accession_number = Column(String(25), nullable=False, index=True)
    target_filing_id = Column(UUID(as_uuid=True), ForeignKey("sec_filings.id"), nullable=True, index=True)
    reference_context = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SECIngestionJob(Base):
    """Background ingestion job for SEC filings."""
    __tablename__ = "sec_ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cik = Column(String(10), nullable=False, index=True)
    accession_number = Column(String(25), nullable=False, index=True)
    form_type = Column(String(20), nullable=False)
    filed_date = Column(Date)
    company_name = Column(String(255))
    filing_url = Column(Text)
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed
    error_message = Column(Text)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
