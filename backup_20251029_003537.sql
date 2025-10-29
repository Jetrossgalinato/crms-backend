--
-- PostgreSQL database dump
--

\restrict eqO47Fj2QjMn31EIimgFkFbAglXXtLP87vaCtwaSMYQnZBOfaguieSn1aOCCN6Z

-- Dumped from database version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account_requests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    email character varying NOT NULL,
    status character varying NOT NULL,
    department character varying,
    phone_number character varying,
    acc_role character varying,
    approved_acc_role character varying,
    is_supervisor boolean NOT NULL,
    is_intern boolean NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.account_requests OWNER TO postgres;

--
-- Name: account_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.account_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.account_requests_id_seq OWNER TO postgres;

--
-- Name: account_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.account_requests_id_seq OWNED BY public.account_requests.id;


--
-- Name: acquiring; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.acquiring (
    id integer NOT NULL,
    acquirers_id integer NOT NULL,
    supply_id integer NOT NULL,
    quantity integer NOT NULL,
    purpose character varying,
    status character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.acquiring OWNER TO postgres;

--
-- Name: acquiring_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.acquiring_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.acquiring_id_seq OWNER TO postgres;

--
-- Name: acquiring_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.acquiring_id_seq OWNED BY public.acquiring.id;


--
-- Name: bookings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bookings (
    id integer NOT NULL,
    bookers_id integer NOT NULL,
    facility_id integer,
    equipment_id integer,
    supply_id integer,
    purpose character varying NOT NULL,
    start_date character varying NOT NULL,
    end_date character varying NOT NULL,
    return_date character varying,
    status character varying NOT NULL,
    request_type character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.bookings OWNER TO postgres;

--
-- Name: bookings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bookings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bookings_id_seq OWNER TO postgres;

--
-- Name: bookings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bookings_id_seq OWNED BY public.bookings.id;


--
-- Name: borrowing; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.borrowing (
    id integer NOT NULL,
    borrowed_item integer NOT NULL,
    borrowers_id integer NOT NULL,
    purpose character varying NOT NULL,
    start_date character varying NOT NULL,
    end_date character varying NOT NULL,
    return_date character varying NOT NULL,
    request_status character varying,
    return_status character varying,
    availability character varying,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.borrowing OWNER TO postgres;

--
-- Name: borrowing_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.borrowing_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.borrowing_id_seq OWNER TO postgres;

--
-- Name: borrowing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.borrowing_id_seq OWNED BY public.borrowing.id;


--
-- Name: done_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.done_notifications (
    id integer NOT NULL,
    booking_id integer NOT NULL,
    completion_notes character varying,
    status character varying NOT NULL,
    message character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.done_notifications OWNER TO postgres;

--
-- Name: done_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.done_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.done_notifications_id_seq OWNER TO postgres;

--
-- Name: done_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.done_notifications_id_seq OWNED BY public.done_notifications.id;


--
-- Name: equipment_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment_logs (
    id integer NOT NULL,
    equipment_id integer,
    action character varying NOT NULL,
    details character varying,
    user_email character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.equipment_logs OWNER TO postgres;

--
-- Name: equipment_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipment_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipment_logs_id_seq OWNER TO postgres;

--
-- Name: equipment_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipment_logs_id_seq OWNED BY public.equipment_logs.id;


--
-- Name: equipments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipments (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    name character varying NOT NULL,
    po_number character varying,
    unit_number character varying,
    brand_name character varying,
    description character varying,
    facility character varying,
    facility_id integer,
    category character varying,
    status character varying,
    date_acquire character varying,
    supplier character varying,
    amount character varying,
    estimated_life character varying,
    item_number character varying,
    property_number character varying,
    control_number character varying,
    serial_number character varying,
    person_liable character varying,
    remarks character varying,
    updated_at timestamp without time zone,
    image character varying
);


ALTER TABLE public.equipments OWNER TO postgres;

--
-- Name: equipments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipments_id_seq OWNER TO postgres;

--
-- Name: equipments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipments_id_seq OWNED BY public.equipments.id;


--
-- Name: facilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.facilities (
    facility_id integer NOT NULL,
    facility_name character varying NOT NULL,
    facility_type character varying NOT NULL,
    floor_level character varying NOT NULL,
    capacity integer,
    description character varying,
    status character varying NOT NULL,
    image_url character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    connection_type character varying,
    cooling_tools character varying,
    building character varying,
    remarks character varying
);


ALTER TABLE public.facilities OWNER TO postgres;

--
-- Name: facilities_facility_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.facilities_facility_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.facilities_facility_id_seq OWNER TO postgres;

--
-- Name: facilities_facility_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.facilities_facility_id_seq OWNED BY public.facilities.facility_id;


--
-- Name: facility_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.facility_logs (
    id integer NOT NULL,
    facility_id integer,
    action character varying NOT NULL,
    details character varying,
    user_email character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.facility_logs OWNER TO postgres;

--
-- Name: facility_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.facility_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.facility_logs_id_seq OWNER TO postgres;

--
-- Name: facility_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.facility_logs_id_seq OWNED BY public.facility_logs.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying NOT NULL,
    message character varying NOT NULL,
    type character varying NOT NULL,
    is_read boolean NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: return_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.return_notifications (
    id integer NOT NULL,
    borrowing_id integer NOT NULL,
    receiver_name character varying NOT NULL,
    status character varying NOT NULL,
    message character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.return_notifications OWNER TO postgres;

--
-- Name: return_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.return_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.return_notifications_id_seq OWNER TO postgres;

--
-- Name: return_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.return_notifications_id_seq OWNED BY public.return_notifications.id;


--
-- Name: supplies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.supplies (
    supply_id integer NOT NULL,
    supply_name character varying NOT NULL,
    description character varying,
    category character varying NOT NULL,
    quantity integer NOT NULL,
    stocking_point integer NOT NULL,
    stock_unit character varying NOT NULL,
    facility_id integer,
    remarks character varying,
    image_url character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.supplies OWNER TO postgres;

--
-- Name: supplies_supply_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.supplies_supply_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.supplies_supply_id_seq OWNER TO postgres;

--
-- Name: supplies_supply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.supplies_supply_id_seq OWNED BY public.supplies.supply_id;


--
-- Name: supply_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.supply_logs (
    id integer NOT NULL,
    supply_id integer,
    action character varying NOT NULL,
    details character varying,
    user_email character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.supply_logs OWNER TO postgres;

--
-- Name: supply_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.supply_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.supply_logs_id_seq OWNER TO postgres;

--
-- Name: supply_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.supply_logs_id_seq OWNED BY public.supply_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    department character varying NOT NULL,
    phone_number character varying NOT NULL,
    acc_role character varying NOT NULL,
    status character varying NOT NULL,
    is_employee boolean NOT NULL,
    is_approved boolean NOT NULL,
    hashed_password character varying NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: account_requests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_requests ALTER COLUMN id SET DEFAULT nextval('public.account_requests_id_seq'::regclass);


--
-- Name: acquiring id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acquiring ALTER COLUMN id SET DEFAULT nextval('public.acquiring_id_seq'::regclass);


--
-- Name: bookings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings ALTER COLUMN id SET DEFAULT nextval('public.bookings_id_seq'::regclass);


--
-- Name: borrowing id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowing ALTER COLUMN id SET DEFAULT nextval('public.borrowing_id_seq'::regclass);


--
-- Name: done_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.done_notifications ALTER COLUMN id SET DEFAULT nextval('public.done_notifications_id_seq'::regclass);


--
-- Name: equipment_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_logs ALTER COLUMN id SET DEFAULT nextval('public.equipment_logs_id_seq'::regclass);


--
-- Name: equipments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipments ALTER COLUMN id SET DEFAULT nextval('public.equipments_id_seq'::regclass);


--
-- Name: facilities facility_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facilities ALTER COLUMN facility_id SET DEFAULT nextval('public.facilities_facility_id_seq'::regclass);


--
-- Name: facility_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facility_logs ALTER COLUMN id SET DEFAULT nextval('public.facility_logs_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: return_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.return_notifications ALTER COLUMN id SET DEFAULT nextval('public.return_notifications_id_seq'::regclass);


--
-- Name: supplies supply_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supplies ALTER COLUMN supply_id SET DEFAULT nextval('public.supplies_supply_id_seq'::regclass);


--
-- Name: supply_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supply_logs ALTER COLUMN id SET DEFAULT nextval('public.supply_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: account_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account_requests (id, user_id, first_name, last_name, email, status, department, phone_number, acc_role, approved_acc_role, is_supervisor, is_intern, created_at) FROM stdin;
2	2	Jetross	Neri	jetrossneri07@gmail.com	Approved	BSIT	09705872970	Lab Technician	Super Admin	f	f	2025-10-24 09:01:37.366284
\.


--
-- Data for Name: acquiring; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.acquiring (id, acquirers_id, supply_id, quantity, purpose, status, created_at, updated_at) FROM stdin;
3	1	1	1	for writing	Approved	2025-10-24 03:47:18.523296	2025-10-24 03:52:23.549016
\.


--
-- Data for Name: bookings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bookings (id, bookers_id, facility_id, equipment_id, supply_id, purpose, start_date, end_date, return_date, status, request_type, created_at, updated_at) FROM stdin;
8	1	1	\N	\N	for a meeting	2025-10-24	2025-10-24	\N	Completed	Facility	2025-10-24 03:43:09.202953	2025-10-24 03:45:30.463467
\.


--
-- Data for Name: borrowing; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.borrowing (id, borrowed_item, borrowers_id, purpose, start_date, end_date, return_date, request_status, return_status, availability, created_at) FROM stdin;
4	1	1	for gaming	2025-10-24	2025-10-31	2025-10-30	Approved	Returned	Available	2025-10-24 03:02:52.215672
\.


--
-- Data for Name: done_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.done_notifications (id, booking_id, completion_notes, status, message, created_at) FROM stdin;
1	8	great	confirmed	Booking completed by jetrossgalinato@gmail.com	2025-10-24 03:44:55.481581
\.


--
-- Data for Name: equipment_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipment_logs (id, equipment_id, action, details, user_email, created_at) FROM stdin;
1	1	Borrowing Approved	Borrowing request ID 4 approved for Lenovo Legion 7i	jetrossgalinato@gmail.com	2025-10-24 03:04:11.591812
2	1	Return Confirmed	Equipment return confirmed for borrowing ID 4	jetrossgalinato@gmail.com	2025-10-24 03:33:47.575143
\.


--
-- Data for Name: equipments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipments (id, created_at, name, po_number, unit_number, brand_name, description, facility, facility_id, category, status, date_acquire, supplier, amount, estimated_life, item_number, property_number, control_number, serial_number, person_liable, remarks, updated_at, image) FROM stdin;
1	2025-10-22 16:04:53.164254	Lenovo Legion 7i	PO-12616271671	UN-1y82178721	Lenovo	Great gaming laptop	\N	1	Laptop	Working	2025-10-23	Lenovo Industries	130000	10 yrs	IN-118278172	PN-121872817	CN-819281982	SN-18281827817	Ronnel Cacho	don't overuse	2025-10-22 17:38:35.035554	http://localhost:8000/uploads/equipment-images/1761149093-ac4bc964.jpeg
\.


--
-- Data for Name: facilities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.facilities (facility_id, facility_name, facility_type, floor_level, capacity, description, status, image_url, created_at, updated_at, connection_type, cooling_tools, building, remarks) FROM stdin;
1	AIR LAB	Robotic Hub	1st Floor	10	\N	Available	\N	2025-10-22 16:49:10.814055	\N	Wi-Fi	Aircon	HIRAYA	Great
\.


--
-- Data for Name: facility_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.facility_logs (id, facility_id, action, details, user_email, created_at) FROM stdin;
1	1	Booking Approved	Booking request ID 8 approved	jetrossgalinato@gmail.com	2025-10-24 03:44:17.384941
2	1	Booking Completed	Booking completion confirmed for booking ID 8	jetrossgalinato@gmail.com	2025-10-24 03:45:30.463647
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, user_id, title, message, type, is_read, created_at) FROM stdin;
3	1	Borrowing Request Approved	Your borrowing request for equipment has been approved	info	t	2025-10-24 03:04:11.578558
4	1	Equipment Return Notification	User jetrossgalinato@gmail.com reported equipment return. Receiver: Ronnel Cacho	info	t	2025-10-24 03:04:59.48378
5	1	Equipment Return Confirmed	Your equipment return has been confirmed	success	t	2025-10-24 03:33:47.575001
6	1	Booking Request Approved	Your facility booking request has been approved	info	t	2025-10-24 03:44:17.384814
7	1	Booking Completion Notification	User jetrossgalinato@gmail.com marked booking as done. Notes: great	info	t	2025-10-24 03:44:55.481691
8	1	Booking Completion Confirmed	Your booking completion has been confirmed	success	t	2025-10-24 03:45:30.463495
9	1	Acquiring Request Approved	Your supply acquiring request has been approved	info	t	2025-10-24 03:52:23.549025
\.


--
-- Data for Name: return_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.return_notifications (id, borrowing_id, receiver_name, status, message, created_at) FROM stdin;
1	4	Ronnel Cacho	confirmed	Equipment returned by jetrossgalinato@gmail.com	2025-10-24 03:04:59.483615
\.


--
-- Data for Name: supplies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.supplies (supply_id, supply_name, description, category, quantity, stocking_point, stock_unit, facility_id, remarks, image_url, created_at, updated_at) FROM stdin;
1	Bond Paper A4	\N	MISC	99	20	ream	1	cool	http://localhost:8000/uploads/supply-images/f9a72029-72ac-4a1a-bfb3-306eaded7261.jpg	2025-10-22 17:47:49.662907	2025-10-24 03:52:23.549001
\.


--
-- Data for Name: supply_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.supply_logs (id, supply_id, action, details, user_email, created_at) FROM stdin;
1	1	Acquiring Approved	Acquiring request ID 3 approved, quantity: 1	jetrossgalinato@gmail.com	2025-10-24 03:52:23.549115
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, first_name, last_name, department, phone_number, acc_role, status, is_employee, is_approved, hashed_password) FROM stdin;
1	jetrossgalinato@gmail.com	Jetross Axle	Galinato	BSIT	09705872979	CCIS Dean	Pending	t	t	$2b$12$//qmzn1CbiTEgAyYaFJ7QepXkXwmlxk8oWalRAfcQ7qmKFiDy.b1W
2	jetrossneri07@gmail.com	Jetross	Neri	BSIT	09705872979	Super Admin	Approved	t	t	$2b$12$9tc/uGEfVVuRocK.miNDvO.BF68zlfU5fMTrpbAXj.5RpK1dncYza
\.


--
-- Name: account_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.account_requests_id_seq', 2, true);


--
-- Name: acquiring_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.acquiring_id_seq', 4, true);


--
-- Name: bookings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bookings_id_seq', 8, true);


--
-- Name: borrowing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.borrowing_id_seq', 5, true);


--
-- Name: done_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.done_notifications_id_seq', 1, true);


--
-- Name: equipment_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipment_logs_id_seq', 2, true);


--
-- Name: equipments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipments_id_seq', 1, true);


--
-- Name: facilities_facility_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.facilities_facility_id_seq', 1, true);


--
-- Name: facility_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.facility_logs_id_seq', 2, true);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_id_seq', 9, true);


--
-- Name: return_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.return_notifications_id_seq', 1, true);


--
-- Name: supplies_supply_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.supplies_supply_id_seq', 1, true);


--
-- Name: supply_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.supply_logs_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: account_requests account_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_requests
    ADD CONSTRAINT account_requests_pkey PRIMARY KEY (id);


--
-- Name: acquiring acquiring_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acquiring
    ADD CONSTRAINT acquiring_pkey PRIMARY KEY (id);


--
-- Name: bookings bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: borrowing borrowing_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowing
    ADD CONSTRAINT borrowing_pkey PRIMARY KEY (id);


--
-- Name: done_notifications done_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.done_notifications
    ADD CONSTRAINT done_notifications_pkey PRIMARY KEY (id);


--
-- Name: equipment_logs equipment_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_logs
    ADD CONSTRAINT equipment_logs_pkey PRIMARY KEY (id);


--
-- Name: equipments equipments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipments
    ADD CONSTRAINT equipments_pkey PRIMARY KEY (id);


--
-- Name: facilities facilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facilities
    ADD CONSTRAINT facilities_pkey PRIMARY KEY (facility_id);


--
-- Name: facility_logs facility_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facility_logs
    ADD CONSTRAINT facility_logs_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: return_notifications return_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.return_notifications
    ADD CONSTRAINT return_notifications_pkey PRIMARY KEY (id);


--
-- Name: supplies supplies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supplies
    ADD CONSTRAINT supplies_pkey PRIMARY KEY (supply_id);


--
-- Name: supply_logs supply_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supply_logs
    ADD CONSTRAINT supply_logs_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_account_requests_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_account_requests_id ON public.account_requests USING btree (id);


--
-- Name: ix_acquiring_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_acquiring_id ON public.acquiring USING btree (id);


--
-- Name: ix_bookings_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bookings_id ON public.bookings USING btree (id);


--
-- Name: ix_borrowing_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_borrowing_id ON public.borrowing USING btree (id);


--
-- Name: ix_done_notifications_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_done_notifications_id ON public.done_notifications USING btree (id);


--
-- Name: ix_equipment_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_equipment_logs_id ON public.equipment_logs USING btree (id);


--
-- Name: ix_equipments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_equipments_id ON public.equipments USING btree (id);


--
-- Name: ix_facilities_facility_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_facilities_facility_id ON public.facilities USING btree (facility_id);


--
-- Name: ix_facility_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_facility_logs_id ON public.facility_logs USING btree (id);


--
-- Name: ix_notifications_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_id ON public.notifications USING btree (id);


--
-- Name: ix_return_notifications_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_return_notifications_id ON public.return_notifications USING btree (id);


--
-- Name: ix_supplies_supply_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_supplies_supply_id ON public.supplies USING btree (supply_id);


--
-- Name: ix_supply_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_supply_logs_id ON public.supply_logs USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: acquiring acquiring_acquirers_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acquiring
    ADD CONSTRAINT acquiring_acquirers_id_fkey FOREIGN KEY (acquirers_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: acquiring acquiring_supply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acquiring
    ADD CONSTRAINT acquiring_supply_id_fkey FOREIGN KEY (supply_id) REFERENCES public.supplies(supply_id) ON DELETE CASCADE;


--
-- Name: bookings bookings_bookers_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_bookers_id_fkey FOREIGN KEY (bookers_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: bookings bookings_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(facility_id) ON DELETE CASCADE;


--
-- Name: borrowing borrowing_borrowed_item_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowing
    ADD CONSTRAINT borrowing_borrowed_item_fkey FOREIGN KEY (borrowed_item) REFERENCES public.equipments(id) ON DELETE CASCADE;


--
-- Name: done_notifications done_notifications_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.done_notifications
    ADD CONSTRAINT done_notifications_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE CASCADE;


--
-- Name: equipment_logs equipment_logs_equipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_logs
    ADD CONSTRAINT equipment_logs_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES public.equipments(id);


--
-- Name: facility_logs facility_logs_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facility_logs
    ADD CONSTRAINT facility_logs_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(facility_id);


--
-- Name: return_notifications return_notifications_borrowing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.return_notifications
    ADD CONSTRAINT return_notifications_borrowing_id_fkey FOREIGN KEY (borrowing_id) REFERENCES public.borrowing(id) ON DELETE CASCADE;


--
-- Name: supplies supplies_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supplies
    ADD CONSTRAINT supplies_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(facility_id);


--
-- Name: supply_logs supply_logs_supply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supply_logs
    ADD CONSTRAINT supply_logs_supply_id_fkey FOREIGN KEY (supply_id) REFERENCES public.supplies(supply_id);


--
-- PostgreSQL database dump complete
--

\unrestrict eqO47Fj2QjMn31EIimgFkFbAglXXtLP87vaCtwaSMYQnZBOfaguieSn1aOCCN6Z

