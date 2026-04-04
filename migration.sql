DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

CREATE TABLE admin_users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(32) NOT NULL CHECK (role IN ('superadmin', 'admin', 'editor')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE merchants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    type VARCHAR(32) NOT NULL CHECK (type IN ('Self Managed', 'Semi-Autopilot', 'Full-Autopilot', 'Auto Pilot')),
    logo_url TEXT,
    logo_base64 TEXT,
    bep_months INTEGER NOT NULL CHECK (bep_months > 0),
    rating NUMERIC(2,1),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_top_merchant BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE merchant_packages (
    id UUID PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    price BIGINT NOT NULL CHECK (price > 0),
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_merchant_packages_merchant_id ON merchant_packages (merchant_id);

CREATE TABLE insight_articles (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    author VARCHAR(255) NOT NULL,
    image TEXT,
    image_base64 TEXT,
    excerpt TEXT NOT NULL,
    read_time VARCHAR(64) NOT NULL,
    content JSONB NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('draft', 'published', 'archived')),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE carousel_items (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    image_url TEXT,
    image_base64 TEXT,
    tag VARCHAR(100) NOT NULL,
    icon VARCHAR(64) NOT NULL DEFAULT 'trending-up',
    highlight VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    color VARCHAR(128) NOT NULL,
    cta_label VARCHAR(100) NOT NULL DEFAULT 'Pelajari Lebih Lanjut',
    cta_href TEXT NOT NULL DEFAULT '/merchants',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE client_users (
    id UUID PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(32) NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_client_users_email ON client_users (email);

CREATE TABLE client_merchant_applications (
    id UUID PRIMARY KEY,
    client_user_id UUID REFERENCES client_users(id) ON DELETE SET NULL,
    contact_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(32) NOT NULL,
    category VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    message TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_client_merchant_applications_client_user_id ON client_merchant_applications (client_user_id);

CREATE TABLE client_merchant_inquiries (
    id UUID PRIMARY KEY,
    client_user_id UUID NOT NULL REFERENCES client_users(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    package_name VARCHAR(255),
    inquiry_type VARCHAR(32) NOT NULL DEFAULT 'contact',
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(32) NOT NULL,
    message TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_client_merchant_inquiries_client_user_id ON client_merchant_inquiries (client_user_id);
CREATE INDEX ix_client_merchant_inquiries_merchant_id ON client_merchant_inquiries (merchant_id);

CREATE TABLE alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('0004_image_base64_assets');
