<script lang="ts">
	import { page } from '$app/state';
	import { Filemanager, Willow } from '@svar-ui/svelte-filemanager';
	import type { IApi, IEntity, IFile, TID } from '@svar-ui/svelte-filemanager';

	type FMItemType = 'file' | 'folder';

	type ListResponse = {
		path: string;
		items: Array<{
			id: string;
			type: FMItemType;
			name: string;
			size?: number;
			date?: string;
		}>;
	};

	type DriveInfo = {
		used?: number;
		total?: number;
	};

	let editId = $derived<number | null>(
		(() => {
			const raw = page.url.searchParams.get('edit');
			if (!raw) return null;
			const n = Number(raw);
			return Number.isFinite(n) && n > 0 ? n : null;
		})()
	);

	let cwd = $state<string>('/');
	let items = $state<IEntity[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let drive = $state<DriveInfo>({});
	let fmApi = $state<IApi | null>(null);

	$effect(() => {
		const id = editId;
		if (!id) {
			items = [];
			cwd = '/';
			error = null;
			return;
		}
		void loadDir(id, '/');
	});

	function parseDate(s?: string): Date | undefined {
		if (!s) return undefined;
		const d = new Date(s);
		return Number.isNaN(d.getTime()) ? undefined : d;
	}

	function normalizePath(p: string): string {
		if (!p) return '/';
		if (!p.startsWith('/')) p = '/' + p;
		if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);
		return p;
	}

	function toEntities(items: ListResponse['items']): IEntity[] {
		return items.map((it) => ({
			id: it.id,
			type: it.type,
			name: it.name,
			size: it.size,
			date: parseDate(it.date),
			lazy: it.type === 'folder'
		}));
	}

	async function api<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
		const res = await fetch(input, {
			credentials: 'include',
			...(init ?? {}),
			headers: {
				accept: 'application/json',
				...(init?.headers ?? {})
			}
		});

		if (!res.ok) {
			const text = await res.text();
			throw new Error(text || `Request failed (${res.status})`);
		}

		return (await res.json()) as T;
	}

	async function fetchEntities(id: number, path: string): Promise<IEntity[]> {
		const url = `/api/pages/${id}/files?path=${encodeURIComponent(normalizePath(path))}`;
		const data = await api<ListResponse>(url, { method: 'GET' });
		return toEntities(data.items);
	}

	async function loadDir(id: number, path: string) {
		loading = true;
		error = null;

		try {
			const url = `/api/pages/${id}/files?path=${encodeURIComponent(normalizePath(path))}`;
			const data = await api<ListResponse>(url, { method: 'GET' });

			cwd = normalizePath(data.path);
			items = toEntities(data.items);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function createFolder(parentPath: string, name: string) {
		const id = editId;
		if (!id) return;

		await api(`/api/pages/${id}/files/folder`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ path: normalizePath(parentPath), name })
		});
	}

	async function renameItem(path: string, newName: string) {
		const id = editId;
		if (!id) return;

		await api(`/api/pages/${id}/files/rename`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ path: normalizePath(path), new_name: newName })
		});
	}

	async function deleteItems(paths: string[]) {
		const id = editId;
		if (!id) return;

		await api(`/api/pages/${id}/files/delete`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ paths: paths.map((p) => normalizePath(p)) })
		});
	}

	async function moveItem(src: string, dstDir: string) {
		const id = editId;
		if (!id) return;

		await api(`/api/pages/${id}/files/move`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ src: normalizePath(src), dst_dir: normalizePath(dstDir) })
		});
	}

	async function copyItem(src: string, dstDir: string) {
		const id = editId;
		if (!id) return;

		await api(`/api/pages/${id}/files/copy`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ src: normalizePath(src), dst_dir: normalizePath(dstDir) })
		});
	}

	async function uploadFile(targetDir: string, file: File) {
		const id = editId;
		if (!id) return;

		const fd = new FormData();
		fd.append('file', file);

		const url = `/api/pages/${id}/files/upload?path=${encodeURIComponent(normalizePath(targetDir))}`;
		await api(url, {
			method: 'POST',
			body: fd
		});
	}

	async function createEmptyFile(targetDir: string, name: string) {
		const id = editId;
		if (!id) return;

		await api(`/api/pages/${id}/files/empty`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ path: normalizePath(targetDir), name })
		});
	}

	function downloadUrl(path: string) {
		const id = editId;
		if (!id) return '#';
		return `/api/pages/${id}/files/download?path=${encodeURIComponent(normalizePath(path))}`;
	}

	async function provideData(path: string) {
		const id = editId;
		const apiRef = fmApi;
		if (!id || !apiRef) return;

		const data = await fetchEntities(id, path);
		await apiRef.exec('provide-data', { id: normalizePath(path), data });
	}

	function init(apiRef: IApi) {
		fmApi = apiRef;
	}

	async function handleRequestData(ev: { id: TID }) {
		await provideData(String(ev.id || '/'));
	}

	async function handleCreateFile(ev: { file: IFile; parent: TID }) {
		const parent = String(ev.parent || '/');
		if (ev.file.type === 'folder') {
			await createFolder(parent, ev.file.name);
		} else if (ev.file.file) {
			await uploadFile(parent, ev.file.file);
		} else if (ev.file.file === undefined) {
			await createEmptyFile(parent, ev.file.name);
		} else {
			throw new Error('No file data to upload');
		}
		await provideData(parent);
		await loadDir(editId ?? 0, parent);
	}

	async function handleRenameFile(ev: { id: TID; name: string }) {
		const id = String(ev.id);
		await renameItem(id, ev.name);
		const parent = normalizePath(id.split('/').slice(0, -1).join('/') || '/');
		await provideData(parent);
		await loadDir(editId ?? 0, parent);
	}

	async function handleDeleteFiles(ev: { ids: TID[] }) {
		const ids = ev.ids.map((id) => String(id));
		await deleteItems(ids);
		await provideData(cwd);
		await loadDir(editId ?? 0, cwd);
	}

	async function handleMoveFiles(ev: { ids: TID[]; target: TID }) {
		const target = String(ev.target);
		for (const id of ev.ids) {
			await moveItem(String(id), target);
		}
		await provideData(target);
		await loadDir(editId ?? 0, target);
	}

	async function handleCopyFiles(ev: { ids: TID[]; target: TID }) {
		const target = String(ev.target);
		for (const id of ev.ids) {
			await copyItem(String(id), target);
		}
		await provideData(target);
		await loadDir(editId ?? 0, target);
	}

	function handleDownloadFile(ev: { id: TID }) {
		window.location.href = downloadUrl(String(ev.id));
	}
</script>

{#if !editId}
	<p>Select a page to edit to manage its files.</p>
{:else}
	{#if error}
		<p>{error}</p>
	{/if}

	{#if loading}
		<p>Loading...</p>
	{/if}

	<Willow>
		<Filemanager
			data={items}
			{drive}
			{init}
			onrequestdata={handleRequestData}
			oncreatefile={handleCreateFile}
			onrenamefile={handleRenameFile}
			ondeletefiles={handleDeleteFiles}
			onmovefiles={handleMoveFiles}
			oncopyfiles={handleCopyFiles}
			ondownloadfile={handleDownloadFile}
		/>
	</Willow>
{/if}
