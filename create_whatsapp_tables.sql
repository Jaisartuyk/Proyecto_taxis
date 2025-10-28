-- Script SQL para crear tablas de WhatsApp manualmente
-- Ejecutar en Railway Database si las migraciones no funcionan

-- Tabla: WhatsAppConversation
CREATE TABLE IF NOT EXISTS taxis_whatsappconversation (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES taxis_appuser(id) ON DELETE CASCADE NULL,
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    state VARCHAR(30) NOT NULL DEFAULT 'inicio',
    data JSONB NOT NULL DEFAULT '{}',
    ride_id INTEGER REFERENCES taxis_ride(id) ON DELETE SET NULL NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_conv_phone ON taxis_whatsappconversation(phone_number);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conv_status ON taxis_whatsappconversation(status);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conv_user ON taxis_whatsappconversation(user_id);

-- Tabla: WhatsAppMessage
CREATE TABLE IF NOT EXISTS taxis_whatsappmessage (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES taxis_whatsappconversation(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    message_id VARCHAR(255),
    delivered BOOLEAN NOT NULL DEFAULT FALSE,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_msg_conv ON taxis_whatsappmessage(conversation_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_msg_created ON taxis_whatsappmessage(created_at);

-- Tabla: WhatsAppStats
CREATE TABLE IF NOT EXISTS taxis_whatsappstats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_messages INTEGER NOT NULL DEFAULT 0,
    incoming_messages INTEGER NOT NULL DEFAULT 0,
    outgoing_messages INTEGER NOT NULL DEFAULT 0,
    new_conversations INTEGER NOT NULL DEFAULT 0,
    active_conversations INTEGER NOT NULL DEFAULT 0,
    completed_conversations INTEGER NOT NULL DEFAULT 0,
    rides_requested INTEGER NOT NULL DEFAULT 0,
    rides_completed INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_stats_date ON taxis_whatsappstats(date);

-- Verificar tablas creadas
SELECT tablename FROM pg_tables WHERE tablename LIKE 'taxis_whatsapp%';
