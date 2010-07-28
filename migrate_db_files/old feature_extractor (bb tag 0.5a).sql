--
-- PostgreSQL database dump
--

-- Started on 2010-07-15 19:01:23

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 1559 (class 1259 OID 55757)
-- Dependencies: 3
-- Name: feature_extractor; Type: TABLE; Schema: public; Owner: gordon; Tablespace: 
--

CREATE TABLE feature_extractor (
    id integer NOT NULL,
    name character varying(256),
    description text,
    fname character varying(256),
    fdefcode text
);


ALTER TABLE public.feature_extractor OWNER TO gordon;

--
-- TOC entry 1558 (class 1259 OID 55755)
-- Dependencies: 3 1559
-- Name: feature_extractor_id_seq; Type: SEQUENCE; Schema: public; Owner: gordon
--

CREATE SEQUENCE feature_extractor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.feature_extractor_id_seq OWNER TO gordon;

--
-- TOC entry 1844 (class 0 OID 0)
-- Dependencies: 1558
-- Name: feature_extractor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gordon
--

ALTER SEQUENCE feature_extractor_id_seq OWNED BY feature_extractor.id;


--
-- TOC entry 1845 (class 0 OID 0)
-- Dependencies: 1558
-- Name: feature_extractor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gordon
--

SELECT pg_catalog.setval('feature_extractor_id_seq', 6, true);


--
-- TOC entry 1837 (class 2604 OID 55760)
-- Dependencies: 1559 1558 1559
-- Name: id; Type: DEFAULT; Schema: public; Owner: gordon
--

ALTER TABLE feature_extractor ALTER COLUMN id SET DEFAULT nextval('feature_extractor_id_seq'::regclass);


--
-- TOC entry 1841 (class 0 OID 55757)
-- Dependencies: 1559
-- Data for Name: feature_extractor; Type: TABLE DATA; Schema: public; Owner: gordon
--

COPY feature_extractor (id, name, description, fname, fdefcode) FROM stdin;
6	stft	@author: Ron Weiss\n    Compute short-time Fourier transform.\nparams: track, nfft, nwin=None, nhop=None\nimports frontend (http://github.com/ronw/frontend)	stft	def stft(track, nfft, nwin=None, nhop=None):\n    """@author: Ron Weiss\n    Compute short-time Fourier transform."""\n    import frontend as fe\n    pipeline = fe.Pipeline(fe.AudioSource(track.fn_audio), fe.Mono(),\n                           fe.STFT(nfft=nfft, nwin=nwin, nhop=nhop))\n    return pipeline.toarray().T
3	return zero	returns 0	return_zero	def return_zero(track): return 0
1	test 1	an empty feature extractor record	\N	\N
5	mathtest	Returns a tuple with:\n system version; and\n the track's sampling rate natural log\n@author: Jorge Orpinel	mathtest	def mathtest(track):\n    import sys, math\n    return [sys.version, math.log(track.audio()[1])]
4	RMS energy 1.0	Returns the RMS energy in dB of the entire track.\n@author: Ron Weiss	compute_rms_energy	def compute_rms_energy(track):\n    import numpy as np\n    """@author: Ron Weiss\n    @param track: a gordon.Track\n    Returns the RMS energy in dB of the entire track."""\n    \n    samples, fs, svals = track.audio()\n    return 20*np.log10(np.sqrt(np.mean(samples**2)))
\.


--
-- TOC entry 1839 (class 2606 OID 55765)
-- Dependencies: 1559 1559
-- Name: feature_extractor_pkey; Type: CONSTRAINT; Schema: public; Owner: gordon; Tablespace: 
--

ALTER TABLE ONLY feature_extractor
    ADD CONSTRAINT feature_extractor_pkey PRIMARY KEY (id);


--
-- TOC entry 1840 (class 1259 OID 55766)
-- Dependencies: 1559
-- Name: ix_feature_extractor_id; Type: INDEX; Schema: public; Owner: gordon; Tablespace: 
--

CREATE UNIQUE INDEX ix_feature_extractor_id ON feature_extractor USING btree (id);


-- Completed on 2010-07-15 19:01:24

--
-- PostgreSQL database dump complete
--

