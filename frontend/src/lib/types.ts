export type User = {
	id: number | string;
	username: string;
	role: number;
};

export type Page = {
	id: number | string;
	name: string | null;
	external_url: string;
	is_private: boolean | null;
	role: number;
};
