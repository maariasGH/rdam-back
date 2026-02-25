--
-- PostgreSQL database dump
--

\restrict 8SN6YViwgzygcS0sg3uK3bvVbLhMq142MF9ZNv8amsH6xE7DxSVjNx1EQeSXFML

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

-- Started on 2026-02-25 18:11:36

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5072 (class 1262 OID 16388)
-- Name: rdam_db; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE rdam_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'es-AR';


ALTER DATABASE rdam_db OWNER TO postgres;

\unrestrict 8SN6YViwgzygcS0sg3uK3bvVbLhMq142MF9ZNv8amsH6xE7DxSVjNx1EQeSXFML
\connect rdam_db
\restrict 8SN6YViwgzygcS0sg3uK3bvVbLhMq142MF9ZNv8amsH6xE7DxSVjNx1EQeSXFML

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 859 (class 1247 OID 16390)
-- Name: estado_tramite; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.estado_tramite AS ENUM (
    'PENDIENTE',
    'VENCIDO',
    'PAGADO',
    'EMITIDO',
    'RECHAZADO',
    'EMITIDO_VENCIDO'
);


ALTER TYPE public.estado_tramite OWNER TO postgres;

--
-- TOC entry 880 (class 1247 OID 16492)
-- Name: estadotramite; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.estadotramite AS ENUM (
    'PENDIENTE',
    'VENCIDA',
    'PAGADA',
    'EMITIDA',
    'RECHAZADA',
    'EMITIDA_VENCIDA'
);


ALTER TYPE public.estadotramite OWNER TO postgres;

--
-- TOC entry 862 (class 1247 OID 16404)
-- Name: rol_usuario; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.rol_usuario AS ENUM (
    'CIUDADANO',
    'OPERADOR',
    'ADMINISTRADOR'
);


ALTER TYPE public.rol_usuario OWNER TO postgres;

--
-- TOC entry 877 (class 1247 OID 16484)
-- Name: rolusuario; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.rolusuario AS ENUM (
    'CIUDADANO',
    'OPERADOR',
    'ADMINISTRADOR'
);


ALTER TYPE public.rolusuario OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 226 (class 1259 OID 16465)
-- Name: certificados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.certificados (
    certificado_id integer NOT NULL,
    tramite_id integer,
    fecha_emision timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    url_archivo_s3 text
);


ALTER TABLE public.certificados OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16464)
-- Name: certificados_certificado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.certificados_certificado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.certificados_certificado_id_seq OWNER TO postgres;

--
-- TOC entry 5073 (class 0 OID 0)
-- Dependencies: 225
-- Name: certificados_certificado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.certificados_certificado_id_seq OWNED BY public.certificados.certificado_id;


--
-- TOC entry 224 (class 1259 OID 16450)
-- Name: pagos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pagos (
    pago_id integer NOT NULL,
    tramite_id integer,
    external_reference character varying(100),
    monto numeric(10,2) DEFAULT 1250.00,
    fecha_pago timestamp without time zone,
    pagado boolean DEFAULT false
);


ALTER TABLE public.pagos OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16449)
-- Name: pagos_pago_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pagos_pago_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pagos_pago_id_seq OWNER TO postgres;

--
-- TOC entry 5074 (class 0 OID 0)
-- Dependencies: 223
-- Name: pagos_pago_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pagos_pago_id_seq OWNED BY public.pagos.pago_id;


--
-- TOC entry 222 (class 1259 OID 16430)
-- Name: tramites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tramites (
    tramite_id integer NOT NULL,
    cuil character varying(15) NOT NULL,
    nombre_solicitante character varying(100) NOT NULL,
    email_contacto character varying(100) NOT NULL,
    estado public.estado_tramite DEFAULT 'PENDIENTE'::public.estado_tramite,
    fecha_solicitud date DEFAULT CURRENT_DATE,
    usuario_creador_id integer,
    fecha_ultima_modificacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ciudad_solicitante character varying(50) NOT NULL
);


ALTER TABLE public.tramites OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16429)
-- Name: tramites_tramite_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tramites_tramite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tramites_tramite_id_seq OWNER TO postgres;

--
-- TOC entry 5075 (class 0 OID 0)
-- Dependencies: 221
-- Name: tramites_tramite_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tramites_tramite_id_seq OWNED BY public.tramites.tramite_id;


--
-- TOC entry 220 (class 1259 OID 16412)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    usuario_id integer NOT NULL,
    nombre_completo character varying(100) NOT NULL,
    login character varying(50) NOT NULL,
    password_hash text NOT NULL,
    rol public.rol_usuario NOT NULL,
    estado character varying(20) DEFAULT 'Activo'::character varying,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    registrador_id integer
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16411)
-- Name: usuarios_usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_usuario_id_seq OWNER TO postgres;

--
-- TOC entry 5076 (class 0 OID 0)
-- Dependencies: 219
-- Name: usuarios_usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_usuario_id_seq OWNED BY public.usuarios.usuario_id;


--
-- TOC entry 4893 (class 2604 OID 16468)
-- Name: certificados certificado_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificados ALTER COLUMN certificado_id SET DEFAULT nextval('public.certificados_certificado_id_seq'::regclass);


--
-- TOC entry 4890 (class 2604 OID 16453)
-- Name: pagos pago_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos ALTER COLUMN pago_id SET DEFAULT nextval('public.pagos_pago_id_seq'::regclass);


--
-- TOC entry 4886 (class 2604 OID 16433)
-- Name: tramites tramite_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites ALTER COLUMN tramite_id SET DEFAULT nextval('public.tramites_tramite_id_seq'::regclass);


--
-- TOC entry 4883 (class 2604 OID 16415)
-- Name: usuarios usuario_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN usuario_id SET DEFAULT nextval('public.usuarios_usuario_id_seq'::regclass);


--
-- TOC entry 5066 (class 0 OID 16465)
-- Dependencies: 226
-- Data for Name: certificados; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.certificados (certificado_id, tramite_id, fecha_emision, url_archivo_s3) FROM stdin;
\.


--
-- TOC entry 5064 (class 0 OID 16450)
-- Dependencies: 224
-- Data for Name: pagos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pagos (pago_id, tramite_id, external_reference, monto, fecha_pago, pagado) FROM stdin;
\.


--
-- TOC entry 5062 (class 0 OID 16430)
-- Dependencies: 222
-- Data for Name: tramites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tramites (tramite_id, cuil, nombre_solicitante, email_contacto, estado, fecha_solicitud, usuario_creador_id, fecha_ultima_modificacion, ciudad_solicitante) FROM stdin;
1	20334445556	Juan Perez	juan@example.com	PENDIENTE	2026-02-25	2	2026-02-25 17:41:37.510025	Santa Fe
\.


--
-- TOC entry 5060 (class 0 OID 16412)
-- Dependencies: 220
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (usuario_id, nombre_completo, login, password_hash, rol, estado, fecha_creacion, registrador_id) FROM stdin;
1	Admin Sistema	admin	pbkdf2:sha256:250000$xxxx	ADMINISTRADOR	Activo	2026-02-25 17:41:37.504766	\N
2	Juan Perez	jperez	pbkdf2:sha256:250000$yyyy	CIUDADANO	Activo	2026-02-25 17:41:37.508524	\N
\.


--
-- TOC entry 5077 (class 0 OID 0)
-- Dependencies: 225
-- Name: certificados_certificado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.certificados_certificado_id_seq', 1, false);


--
-- TOC entry 5078 (class 0 OID 0)
-- Dependencies: 223
-- Name: pagos_pago_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pagos_pago_id_seq', 1, false);


--
-- TOC entry 5079 (class 0 OID 0)
-- Dependencies: 221
-- Name: tramites_tramite_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tramites_tramite_id_seq', 1, true);


--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 219
-- Name: usuarios_usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_usuario_id_seq', 2, true);


--
-- TOC entry 4907 (class 2606 OID 16474)
-- Name: certificados certificados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificados
    ADD CONSTRAINT certificados_pkey PRIMARY KEY (certificado_id);


--
-- TOC entry 4905 (class 2606 OID 16458)
-- Name: pagos pagos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_pkey PRIMARY KEY (pago_id);


--
-- TOC entry 4903 (class 2606 OID 16443)
-- Name: tramites tramites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_pkey PRIMARY KEY (tramite_id);


--
-- TOC entry 4896 (class 2606 OID 16428)
-- Name: usuarios usuarios_login_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_login_key UNIQUE (login);


--
-- TOC entry 4898 (class 2606 OID 16426)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (usuario_id);


--
-- TOC entry 4899 (class 1259 OID 16480)
-- Name: idx_tramites_cuil; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tramites_cuil ON public.tramites USING btree (cuil);


--
-- TOC entry 4900 (class 1259 OID 16481)
-- Name: idx_tramites_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tramites_estado ON public.tramites USING btree (estado);


--
-- TOC entry 4901 (class 1259 OID 16482)
-- Name: idx_tramites_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tramites_fecha ON public.tramites USING btree (fecha_solicitud);


--
-- TOC entry 4911 (class 2606 OID 16475)
-- Name: certificados certificados_tramite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificados
    ADD CONSTRAINT certificados_tramite_id_fkey FOREIGN KEY (tramite_id) REFERENCES public.tramites(tramite_id);


--
-- TOC entry 4910 (class 2606 OID 16459)
-- Name: pagos pagos_tramite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_tramite_id_fkey FOREIGN KEY (tramite_id) REFERENCES public.tramites(tramite_id) ON DELETE CASCADE;


--
-- TOC entry 4909 (class 2606 OID 16444)
-- Name: tramites tramites_usuario_creador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_usuario_creador_id_fkey FOREIGN KEY (usuario_creador_id) REFERENCES public.usuarios(usuario_id);


--
-- TOC entry 4908 (class 2606 OID 16505)
-- Name: usuarios usuarios_registrador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_registrador_id_fkey FOREIGN KEY (registrador_id) REFERENCES public.usuarios(usuario_id);


-- Completed on 2026-02-25 18:11:36

--
-- PostgreSQL database dump complete
--

\unrestrict 8SN6YViwgzygcS0sg3uK3bvVbLhMq142MF9ZNv8amsH6xE7DxSVjNx1EQeSXFML

